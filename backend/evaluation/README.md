# Evaluation fixture set

`dataset.json` is a fixed, manually curated set of 12 tiny diffs. Five are deterministic-rule cases, three require semantic reasoning, and four are clean or adversarial controls. Run `python evaluation/evaluate.py` from `backend` to evaluate rules offline. Supply recorded, human-reviewed LLM output with `--llm-results` to score LLM findings separately.

The report records category/severity matches, false positives (reported concern for a clean control), and false negatives (missed expected concern). It is a regression aid, not proof of correctness: LLM responses vary with model version, prompts, and incomplete repository context.
