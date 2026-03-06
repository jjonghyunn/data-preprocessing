import os

folder = os.path.dirname(os.path.abspath(__file__))

for filename in os.listdir(folder):
    if filename.endswith('-EMPTY.json'):
        new_name = filename.replace('-EMPTY.json', '.json')
        src = os.path.join(folder, filename)
        dst = os.path.join(folder, new_name)
        os.rename(src, dst)
        print(f'{filename} -> {new_name}')

print('완료')
