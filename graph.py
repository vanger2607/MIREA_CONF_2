import argparse
import sys
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError, field_validator


class ConfigModel(BaseModel):
    # package: обязательно, формат groupId:artifactId — проверяется через pattern
    package: Annotated[
        str,
        Field(
            ...,
            description="Maven coordinate groupId:artifactId",
            pattern=r'^[^:]+:[^:]+$',
        ),
    ]

    # repo: строка, но дополнительная логика проверки ниже (url или path)
    repo: Annotated[str, Field(..., description="Base URL of Maven repo or path to test repo")]

    # version: не пустая строка, по умолчанию "latest"
    version: Annotated[str, Field("latest", min_length=1, description="Version to fetch, or 'latest'")]

    # repo_mode: ограниченный набор значений: auto, url, file
    repo_mode: Annotated[Literal["auto", "url", "file"], Field("auto", description="Mode for repo: 'auto'|'url'|'file'")]

    # ascii_tree: булевый флаг
    ascii_tree: Annotated[bool, Field(False, description="If true, print dependencies as ASCII tree")]

    # проверка допустимости repo_mode
    @field_validator("repo_mode")
    def repo_mode_allowed(cls, v: str) -> str:
        allowed = {"auto", "url", "file"}
        if v not in allowed:
            raise ValueError(f"repo_mode must be one of {sorted(allowed)}")
        return v

    # проверка repo с учётом выбранного repo_mode
    # mode="after" позволяет получить остальные поля через info.data
    @field_validator("repo", mode="after")
    def repo_must_be_valid_for_mode(cls, v: str, info) -> str:
        mode = info.data.get("repo_mode", "auto")
        parsed = urlparse(v)

        def looks_like_url() -> bool:
            return bool(parsed.scheme in ("http", "https") and parsed.netloc)

        def looks_like_path() -> bool:
            try:
                return Path(v).exists()
            except Exception:
                return False

        if mode == "url":
            if not looks_like_url():
                raise ValueError(f"repo must be a valid http(s) URL in repo_mode='url'; got '{v}'")
        elif mode == "file":
            if not looks_like_path():
                raise ValueError(f"repo must be an existing file/directory path in repo_mode='file'; got '{v}'")
        else:  # auto
            if not (looks_like_url() or looks_like_path()):
                raise ValueError(
                    "repo must be either a valid http(s) URL or an existing file/directory path (repo_mode='auto')"
                )
        return v


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="dep", description="packages.")
    parser.add_argument("--package", "-p", type=str, required=True,
                        help="Package coordinate: groupId:artifactId (e.g. com.google.guava:guava)")
    parser.add_argument("--repo", "-r", type=str, required=True,
                        help="Base URL of Maven repo (e.g. https://repo1.maven.org/maven2) or path to test repo")
    parser.add_argument("--version", "-v", type=str, default="latest",
                        help="Version to fetch (or 'latest')")
    parser.add_argument("--repo-mode", "-m", type=str, choices=["auto", "url", "file"], default="auto",
                        help="Mode to interpret --repo: 'auto' (try URL then path), 'url' (force URL), 'file' (force path)")
    parser.add_argument("--ascii-tree", action="store_true",
                        help="Output dependencies in ASCII-tree format (boolean flag)")
    return parser.parse_args(argv)


def print_config(params: dict):
    for k, v in params.items():
        print(f"{k}={v}")


def main(argv=None):
    args = parse_args(argv)

    params = {
        "package": args.package,
        "repo": args.repo,
        "repo_mode": args.repo_mode,
        "version": args.version,
        "ascii_tree": args.ascii_tree,
    }


    print_config(params)

    try:
        cfg = ConfigModel(**params)
    except ValidationError as e:
        print("Validation error:", file=sys.stderr)
        print(e, file=sys.stderr)
        raise SystemExit(2)

    print("\nConfiguration validated successfully. Ready to proceed.")
    return cfg


if __name__ == "__main__":
    main()
