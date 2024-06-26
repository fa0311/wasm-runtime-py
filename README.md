# wasm-runtime-py

Python で WebAssembly バイナリを実行するためのランタイム

## 概要

Wasm を実行するためのランタイムを Python で実装する。

## 設計思想

- 拡張性を重視する
- Windows, macOS, Linux で動作する
- 依存関係の追加は慎重に行う
  - Pydantic は追加しない

## 目標

- SQLite WebAssembly を実行する
- ~~全ての~~ テストケースを通す

## 開発計画

- [] テスト可能な実装にする
- [] テストを通す
  - [] Numeric Instructions の実装
  - [] Control Instructions の実装
    - [] call_indirect の実装
  - [] Memory Instructions の実装
  - [] FC extensions の実装
  - [] SIMD instructions の実装
- [] WASI の実装

## テスト

```sh
# デバッグ
python -m unittest discover -p test_*.py -s tests
# リリース
python -OO -m unittest discover -p test_*.py -s tests
```

<https://pengowray.github.io/wasm-ops/>

<https://zenn.dev/ri5255/articles/bac96cf74f82f0>
