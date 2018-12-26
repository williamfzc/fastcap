# fastcap

> fast screen cap on android, with minicap.

## Installation

```
pip install fastcap
```

## Usage

```python
d = MNCDevice('123456F')
d.screen_shot()
d.export_screen('./aaa.png')
```

and now you will get 'aaa.png' in current directory.

## TODO

File transport is not a perfect way. For further usage, we should replace it with socket.

## License

[MIT](LICENSE)
