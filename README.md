# children-shelter-project

Кошторис дитячого притулку.

## Збірники базових норм ДСТУ Б Д

У каталозі [`dstu-b-d/`](dstu-b-d/):

- **106** збірників Д.2.2–Д.2.4 з роботами та каліброваними ресурсами (~**1145** норм)
- **Поглиблено 44 збірники**: Д.2.2 — 20, Д.2.4 — 18, Д.2.3 — 6 (техчастини, варіанти норм, коефіцієнти)
- Локальний кошторис: `dstu-b-d/exports/lokalnyy-koshtorys-prytulok.csv`
- Відомість ресурсів: `dstu-b-d/exports/vidomist-resursiv-prytulok.csv`
- Зведений кошторисний розрахунок: `dstu-b-d/exports/zvedenyy-koshtorys-prytulok.md`
- Інструкція: [`dstu-b-d/koshtorys-prytulok.md`](dstu-b-d/koshtorys-prytulok.md)

```bash
python3 dstu-b-d/scripts/generate_catalogs.py
```
