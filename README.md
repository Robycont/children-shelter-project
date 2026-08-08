# children-shelter-project

Кошторис дитячого притулку.

## Збірники базових норм ДСТУ Б Д

У каталозі [`dstu-b-d/`](dstu-b-d/):

- **106** збірників Д.2.2–Д.2.4 з роботами та ресурсами (~**1055** норм)
- **Поглиблено 20 збірників**: 1, 6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 20, 21, 22, 23, 26, 27, 46, 47 (техчастина, варіанти норм, коефіцієнти)
- Локальний кошторис: `dstu-b-d/exports/lokalnyy-koshtorys-prytulok.csv`
- Відомість ресурсів: `dstu-b-d/exports/vidomist-resursiv-prytulok.csv`
- Інструкція: [`dstu-b-d/koshtorys-prytulok.md`](dstu-b-d/koshtorys-prytulok.md)

```bash
python3 dstu-b-d/scripts/generate_catalogs.py
```
