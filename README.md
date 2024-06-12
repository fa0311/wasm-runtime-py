# wasm の Python ランタイム

## なぜ Python か

バイト列の扱いが楽で、演算子のオーバーライドができるため可読性を高くしやすい

## 目標

簡単な計算ができるくらいまでは実装したいと思い、再帰的にフィボナッチ数列を計算できる

## 実装した機能

- Type Section
- Function Section
- Export Section
- Code Section
  - スタック
  - 算術演算
  - ローカル変数
  - 関数呼び出し
  - 制御構文

## ファイル構成

- `README.md`: このファイル
- `src`: ソースコード
  - `__main__.py`: エントリーポイント
  - `tools`: ツール
    - `byte.py`: バイト列を簡単に扱うためのツール
    - `formatter.py`: ロガーのフォーマッタ
    - `logger.py`: ロガーのラッパー
  - `wasm`: wasm の実装
    - `loader.py`: wasm ファイルを読み込む
    - `runtime.py`: wasm のランタイム
    - `struct.py`: wasm の構造体
- `assets`: アセット
  - `fibonacci.wat`: フィボナッチ数列の 15 番目を計算する wasm ファイル
  - `fibonacci.wasm`: フィボナッチ数列の 15 番目を計算する wasm ファイルのバイナリ
  - `add.wat`: 1 から 100 までの和を計算する wasm ファイル
  - `add.wasm`: 1 から 100 までの和を計算する wasm ファイルのバイナリ

## 使い方

```sh
$ python3 -V
Python 3.12.3
```

### fibonacci.wasm

```sh
python3 src assets/fibonacci.wasm
```

```log
...
[DEBUG]  ┃┗━[ run ]
[DEBUG]  ┣━ drop: 377 <- これが答え
[DEBUG]  ┣━ end
[DEBUG]  ┣━ return: []
[DEBUG]  ┗━[ run ]
[INFO]   stack: []
```

#### fibonacci.wasm ビルド

22 行目の `i32.const` の数値を変更することで計算するフィボナッチ数列の番号を変更できます。
26 行目の `drop` で計算結果をスタックから削除します。

```sh
wat2wasm assets/fibonacci.wat -o assets/fibonacci.wasm
```

### add.wasm

```sh
python3 src assets/add.wasm
```

```log
...
[DEBUG]  ┃┗━[ run ]
[DEBUG]  ┣━ drop: 5050 <- これが答え
[DEBUG]  ┣━ end
[DEBUG]  ┣━ return: []
[DEBUG]  ┗━[ run ]
[INFO]   stack: []
```

#### add.wasm ビルド

13 行目の `i32.const` の数値を変更することで計算する和の最大値を変更できます。
30 行目の `drop` で計算結果をスタックから削除します。

```sh
wat2wasm assets/add.wat -o assets/add.wasm
```

## 頑張ったところ

デバッグがし易いように、グラフィカルなログが出力される

## 課題

実行が遅い
また、変数が Python の変数実装に依存しているため、オーバーフローしない(i32 が扱える範囲を超える事ができてしまう)

## 参照

<https://pengowray.github.io/wasm-ops/>
