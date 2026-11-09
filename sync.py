"""Serve the exact lowercase URL already configured in the user's Sileo."""
import hashlib
import pathlib
import re
import shutil
import urllib.request

base = 'https://nuloraos.github.io/tweaks/'
root = pathlib.Path('public')
source = root / 'theipos'
source.mkdir(parents=True, exist_ok=True)
def read(name, limit=2*1024*1024):
    with urllib.request.urlopen(base + name, timeout=90) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Response too large')
    return data

index = read('Packages')
for block in index.decode('utf8').split('\n\n'):
    fields = dict(line.split(': ', 1) for line in block.splitlines() if ': ' in line and not line.startswith(' '))
    if not fields.get('Package'):
        continue
    relative = fields['Filename'].removeprefix('./')
    if not re.fullmatch(r'[A-Za-z0-9_./+\-]+', relative) or '..' in relative.split('/') or relative.startswith('/'):
        raise ValueError('Unsafe path')
    data = read(relative, 64*1024*1024)
    if len(data) != int(fields['Size']) or hashlib.sha256(data).hexdigest() != fields['SHA256']:
        raise ValueError('DEB integrity mismatch')
    destination = source / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
for name in ['Release', 'Packages', 'Packages.gz', 'Packages.bz2', 'CydiaIcon.png', 'index.html', 'icon-camera.png', 'icon-o2camera.png', 'icon-dock.png']:
    (source / name).write_bytes(index if name == 'Packages' else read(name))
release = (source / 'Release').read_text()
for name in ['Packages', 'Packages.gz', 'Packages.bz2']:
    data = (source / name).read_bytes()
    if f' {hashlib.sha256(data).hexdigest()} {len(data)} {name}' not in release:
        raise ValueError('APT index integrity mismatch')
# The old address shows the same single list and serves the same one-category APT source.
for entry in source.iterdir():
    if entry.is_dir():
        shutil.copytree(entry, root / entry.name, dirs_exist_ok=True)
    else:
        shutil.copyfile(entry, root / entry.name)
(root / '.nojekyll').touch()
print('Verified source published at /theipos/ and /')
