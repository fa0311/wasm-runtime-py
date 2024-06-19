# wasm-runtime-py

Python で WebAssembly バイナリを実行するためのランタイム

## 設計思想

- 拡張性を重視する
- Windows, macOS, Linux で動作する
- 依存関係の追加は慎重に行う
  - Pydantic は追加しない

## テスト

```sh
# デバッグ
python -m unittest discover -p test_*.py -s tests
# リリース
python -OO -m unittest discover -p test_*.py -s tests
```
