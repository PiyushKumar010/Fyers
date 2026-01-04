import compileall
import pathlib
ok = compileall.compile_dir('app', quiet=1)
out_path = pathlib.Path('backend-compile.log')
out_path.write_text(f'compile_ok={ok}\n', encoding='utf-8')
print(f'compile_ok {ok} -> {out_path.resolve()}')
