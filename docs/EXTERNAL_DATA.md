# External data used by the registered checks (2026-10-02)

Downloaded on 2026-10-02 with the author's approval, kept out of git under
`bench/external/` (see `.gitignore`); the derived samples the scripts build are
committed with their runs. Re-download with the commands below and compare the
SHA-256 values.

| file | source | licence | SHA-256 | used by |
|---|---|---|---|---|
| `bench/external/frank/human_annotations_sentence.json` (9.9 MB) | https://raw.githubusercontent.com/artidoro/frank/main/data/human_annotations_sentence.json (Pagnoni, Balachandran and Tsvetkov, 2021, *Understanding Factuality in Abstractive Summarization with FRANK*) | MIT | `a17c6fb1f66b14e3f2d2c11fa9037839a34fa6c3f4ac3932c1da6a4771ec111f` | `train/run_cell66_check.py` (CELL 66 AMENDMENT) |
| `bench/external/frank/benchmark_data.json` (7.8 MB) | https://raw.githubusercontent.com/artidoro/frank/main/data/benchmark_data.json | MIT | `37b2871cf526cf7726f7cedf017f7abee0e826e709a91501ebbd7f9f644cdc05` | not read by the scripts (the sentence file carries the articles); kept for reference |
| `bench/external/sfu_review/SFU_Review_Corpus_Negation_Speculation.zip` (1.5 MB) | https://www.sfu.ca/~mtaboada/docs/research/SFU_Review_Corpus_Negation_Speculation.zip (Konstantinova, de Sousa, Cruz, Maña, Taboada and Mitkov, 2012, LREC) | GPL-3 (README in the zip) | `a976bc42e2dc461eeafb7f94ceb7aa9b001bc665cbbff1ab9b262594374f7c74` | `train/run_cell62_check.py` (CELL 62 AMENDMENT) |

```bash
mkdir -p bench/external/frank bench/external/sfu_review
curl -sL -o bench/external/frank/human_annotations_sentence.json https://raw.githubusercontent.com/artidoro/frank/main/data/human_annotations_sentence.json
curl -sL -o bench/external/frank/benchmark_data.json https://raw.githubusercontent.com/artidoro/frank/main/data/benchmark_data.json
curl -sL -o bench/external/sfu_review/SFU_Review_Corpus_Negation_Speculation.zip "https://www.sfu.ca/~mtaboada/docs/research/SFU_Review_Corpus_Negation_Speculation.zip"
(cd bench/external/sfu_review && unzip -q -o SFU_Review_Corpus_Negation_Speculation.zip)
shasum -a 256 bench/external/frank/*.json bench/external/sfu_review/*.zip
```

BioScope (Vincze et al., 2008) was considered for Cell 62 and not used: its
host did not answer on 2026-10-02, and product reviews are closer to advisory
prose than biomedical text.
