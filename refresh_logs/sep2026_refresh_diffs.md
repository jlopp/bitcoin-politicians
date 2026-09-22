# September 2026 refresh differences

Comparison of the `Owner = YES` rows in `jlopp/master` before this refresh with the refreshed current-politician table.

## Summary

| | Count |
|---|---:|
| Previous holders | 19 |
| Refreshed current holders | 28 |
| Added | 17 |
| Dropped | 8 |
| Retained | 11 |
| Net change | +9 |

The full summary CSV contains 31 holders: 28 current and 3 past. The public table shows current politicians only.

## Added

| Politician | Matching holding |
|---|---|
| Nicholas J. Begich | Bitcoin and Bitcoin Cash |
| Robert P. Bresnahan | Coinbase stock |
| Gilbert Ray Cisneros | Block, Coinbase, Marathon Digital, and MicroStrategy |
| Byron Donalds | Bitcoin |
| John Fetterman | Coinbase stock |
| Brandon Gill | Bitcoin |
| Pat Harrigan | Ethereum |
| Morgan Luttrell | Fidelity Wise Origin Bitcoin Fund |
| Ryan Mackenzie | Coinbase Bitcoin account |
| Lucy McBath | Coinbase stock |
| Max L. Miller | iShares Bitcoin Trust |
| Jimmy Patronis | Bitcoin |
| Guy Reschenthaler | XRP, Bitcoin, and Solana |
| Tim Sheehy | NYDIG Bitcoin fund |
| Adrian Smith | Bitcoin Bancorp stock |
| Rashida Tlaib | Bitcoin and Ethereum ETFs |
| Derek Tran | Coinbase and Binance crypto wallets |

## Dropped

These five are retained in the full CSV as past politicians but are excluded from the current-politician site table:

- Garret Graves
- Marjorie Taylor Greene
- Jeff Jackson
- J. D. Vance
- Michael Waltz

These three remain current politicians, but their latest processed disclosure does not name the asset that previously produced an owner match:

| Politician | Previous match |
|---|---|
| Lauren Boebert | Coinbase-related asset |
| Daniel S. Goldman | Block and Coinbase stock |
| Josh Gottheimer | Block stock |

Absence from the latest named holdings does not necessarily prove that an asset was sold.

## Retained

- Ashley Arenholz
- Katie Britt
- Mike Collins
- Ted Cruz
- Pat Fallon
- Ro Khanna
- Cynthia Lummis
- David McCormick
- Nancy Pelosi
- Shri Thanedar
- Jefferson Van Drew

Cynthia Lummis is an explicit owner exception. Her latest disclosure lists a qualified blind trust rather than Bitcoin by name, but the tracker retains her as an owner because she previously disclosed Bitcoin moved into that trust.

The image extraction missed holdings in three 2025 House reports, so the underlying filing-level asset data was corrected from the source documents: Ashley Arenholz's Grayscale Bitcoin Mini Trust ETF, Grayscale Bitcoin Trust, and ProShares Bitcoin ETF entries on pages 2–3; Pat Fallon's Block stock on page 8; and Jefferson Van Drew's handwritten Grayscale Investment Trust entry on page 2.
