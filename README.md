# CARO AI PROJECT

Tro choi Caro 9x9 giua nguoi choi va may. Dieu kien thang la 4 quan lien tiep theo hang ngang, hang doc hoac duong cheo, khong xet luat chan hai dau.

## Noi dung da cai dat

- Level 1: AI dung Minimax co gioi han do sau.
- Level 2: AI dung Alpha-Beta pruning, cung ham danh gia va cung do sau voi Minimax.
- Level 3: Benchmark tren 6 trang thai ban co, so sanh node, thoi gian, nuoc di, ty le giam node.
- Nang cao: che do `advanced` dung Alpha-Beta, sap xep nuoc di, bat nuoc thang/chan thang ngay va transposition table.
- Giao dien pygame co chon thuat toan, do sau 1-5, Human/AI di truoc.

## Cau truc

```text
CaroAI_Project/
|-- source_code/
|   |-- ai.py
|   |-- benchmark.py
|   |-- game.py
|   |-- gui_game_data.py
|   |-- gui_pygame.py
|   `-- main.py
|-- requirements.txt
`-- README.md
```

## Cai dat

```bash
pip install -r requirements.txt
```

## Chay console

```bash
python source_code/main.py
```

Console cho phep chon:

- Level 1 Minimax
- Level 2 Alpha-Beta
- Nang cao
- Do sau tim kiem 1, 2, 3, 4, 5
- Human hoac AI di truoc

Luu y: depth 5 lam AI manh hon nhung co the cham voi Minimax. Neu muon choi manh va nhanh hon, nen chon `advanced`.

## Chay giao dien

```bash
python source_code/gui_pygame.py
```

Trong giao dien, bam `Start/Reset` sau khi chon Algorithm, Search depth va First move.

## Chay benchmark Level 3

```bash
python source_code/benchmark.py
```

Benchmark in bang ket qua ra terminal va luu file `benchmark_results.csv` o thu muc project.

## Chay thu thap du lieu tu dong

```bash
python source_code/gui_game_data.py
```

Lenh mac dinh chay console, khong mo man hinh, va chay ca 3 mode:

- Minimax: 100 van
- Alpha-Beta: 100 van
- Advanced: 100 van
- Tong cong: 300 van

File nay chay self-play: X va O deu la search agent dung cung thuat toan, cung depth va cung ham danh gia.

- Depth 1, 2, 3, 4, 5
- Moi depth: AI di truoc 10 van va Human di truoc 10 van
- Tong moi thuat toan: 100 van
- Moi game_index dung mot opening seed khac nhau de 10 van khong trung hoan toan
- Co checkpoint moi 10 van de neu dung giua chung van co file tam
- Candidate cap trong batch hien tai la 3 de Minimax depth 5 chay xong duoc

Ket qua duoc luu trong `game_data_results/`:

- `game_data_raw.csv`: tung van dau
- `game_data_summary.csv`: bang tong hop theo thuat toan, depth, nguoi di truoc
- `game_data_report.txt`: goi y viet phan nhan xet bao cao
