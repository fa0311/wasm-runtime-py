# wasm-runtime-py

Python で WebAssembly バイナリを実行するためのランタイム

## 概要

Wasm を実行するためのランタイムを Python で実装する。

## 設計思想

- 拡張性を重視する
- Windows, macOS, Linux で動作する
- 依存関係の追加は慎重に行う
  - 現在は NumPy のみ
  - Pydantic は追加しない

## 目標

- SQLite WebAssembly を実行する
- ~~全ての~~ テストケースを通す

## 動作推奨環境

- Python 3.12 以上
  - 3.9 - 3.11 では深い再帰でクラッシュする

- NumPy 1.26 以上
  - 古いバージョンで試していない
  - 2.0 でも動作する

- Windows, macOS, Linux
- Intel x86, Apple arm64

## 開発計画

- [ ] テスト可能な実装にする
  - [x] assert_return
  - [x] assert_trap
  - [x] assert_malformed
  - [ ] assert_invalid
- [ ] テストを通す
  - [x] Control Instructions の実装
    - [x] call_indirect の実装
  - [x] Variable Instructions の実装
  - [ ] Table Instructions の実装
  - [ ] Memory Instructions の実装
  - [x] Numeric Instructions の実装
  - [ ] FC extensions の実装
  - [ ] SIMD instructions の実装
- [ ] WASI の実装

## テスト

```sh
# デバッグ
python -m unittest discover -p test_*.py -s tests
# リリース
python -OO -m unittest discover -p test_*.py -s tests
```

## 参考

<https://pengowray.github.io/wasm-ops/>

<https://zenn.dev/ri5255/articles/bac96cf74f82f0>
