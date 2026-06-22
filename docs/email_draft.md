# Draft email to advisor

**Subject:** Contamination project — preliminary results, a GPU request, and one framing question

Hi Professor [Name],

Quick update on the benchmark-contamination-as-a-privacy-vulnerability project, with one decision I'd
like your input on and a request to use the GPU.

**Where it stands.** I've built the full, reproducible pipeline (ground-truth Pythia/Pile membership;
the existing detectors as baselines — LOSS, Min-K%, Min-K%++, zlib; an extraction + PII harness; and a
metrics/statistics layer), reproduced the baselines, and drafted the whole paper (introduction through
conclusion, with a verified related-work comparison table). Every analysis is pre-registered and every
number regenerates from a seeded script.

**Headline preliminary result (stated honestly).** Using a pre-registered partial-correlation and
mediation analysis that controls for raw per-item loss, I find the contamination→leakage association
is essentially all *loss*: the calibrated reference-free detectors (Min-K%, Min-K%++, zlib) add no
predictive value beyond loss for *which items the model actually leaks*. It holds under a non-linear
loss control and under deduplication. One caveat I want to flag up front: these detectors are
statistically collinear with loss, so I'm stating the claim conservatively — "no positive signal
beyond loss," not "they negatively predict leakage." I've framed this as a
*membership-detection-vs-leakage-prediction divergence*: the detectors the field tunes for membership
aren't the right instrument for the privacy/leakage question.

**Honest limitations.** This is on the smallest Pythia (160M) on CPU; extractable memorization is rare
at that scale and PII leakage is a null so far. I also ran an internal adversarial review against the
closest prior work (Al Sahili et al. 2025; Hayes et al., NeurIPS 2025) — it rates the paper a
*borderline* contribution as-is, mainly because the result is preliminary and at a single small model.

**GPU request.** You mentioned a GPU is available — I'd like to use it to scale to Pythia
1.4B/2.8B/6.9B (a one-line config change in my pipeline). That is what tests whether the result
strengthens with scale, produces a non-degenerate extraction outcome, lets me actually measure PII
leakage, and powers the per-domain analysis (which looks like the most promising under-explored angle).

**One question for you.** Given the finding, my plan is to frame the contribution as the security
reframing + a systematic comparison/divergence result (membership detection ≠ leakage prediction),
*not* a new detector — consistent with your "build on what's already shown" guidance. Does that match
what you had in mind, or would you prefer I lean toward proposing a detector improvement?

Happy to share the draft (PDF/HTML), the code repository, and the pre-registration + analysis reports —
just let me know the best format.

Thanks,
[Your name]
