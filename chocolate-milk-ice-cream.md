# Chocolate Milk Ice Cream

**Untested — calculated, not yet made.** Three balanced 1 kg formulas built on Albert Heijn's
high-protein chocolate milk (63% skimmed milk, 35% milk protein, 1.9% cocoa, sweetened with
E954 saccharin and E955 sucralose, 0 g added sugar), plus 35% cream and the stabilizers this
repository models. Sized for a Ninja CREAMi Deluxe as well as a 1 kg batch.

## The problem this carton creates

The milk is already sweet, and none of that sweetness depresses the freezing point.

Saccharin and sucralose are used at milligram doses. They contribute a large amount of
perceived sweetness and effectively **zero PAC**. Meanwhile the only real sugar in the carton
is the 4.6 g/100 ml of native lactose. So a base built on this milk arrives pre-loaded with
sweetness and almost no freezing-point depression — the exact opposite of the usual home
problem, where you add sugar for softness and end up too sweet.

Two consequences drive every formula below:

1. **You still need to reach PAC ≈ 250** for a CREAMi, and the milk gives you only about
   20 of it.
2. **Your POD budget is already ~20–25 units smaller than the 110–120 window**, because the
   calculator cannot see the intense sweeteners. Every gram of PAC you add has to come from
   something with a high PAC-per-POD ratio.

Ranked by PAC/POD, the ingredients in the library that qualify are inulin (6.5), glycerol
(4.6), erythritol (4.3), dextrose (2.7), maltodextrin (1.7). Sucrose is 1.0 and is therefore
a *budget item*, not the workhorse. That single ratio explains the whole ingredient list.

A third consequence is worth stating plainly because it is easy to hope otherwise:
**this does not produce a high-protein ice cream.** The carton is 7.5 g protein per 100 ml,
but ice cream needs fat, sugar and solids that the carton cannot supply, and those dilute it.
All three formulas land at ~4.1% protein, which is about where an ordinary custard base sits.
Pushing cream down to 8% fat only reaches 4.8% protein and drops total solids to 35%, so the
texture cost buys almost nothing. Use this milk because it is low-fat, low-lactose and
convenient, not for the protein.

---

## Entering the carton in the calculator

Use **Ingredients → direct component composition**, not the nutrition-label form. Values are
per 100 g, converted from the per-100 ml label at an estimated density of **1.045 g/ml**
(a ~14% solids, near-zero-fat protein milk is denser than the 1.032 of whole milk).

| Field | Value | Why |
|---|---|---|
| Fat | 0.29 | 0.3 / 1.045 |
| MSNF | **0** | see below |
| Soluble component | **Trehalose** | numeric stand-in for lactose |
| Soluble amount | 4.40 | label sugars 4.6, all of it lactose |
| Fiber | 0.86 | 0.9, from the cocoa |
| Other solids | 8.33 | protein 7.18 + non-sugar carb 0.19 + estimated ash 0.96 |
| Salt | 0 | folded into other solids — see caveats |
| Alcohol / Gums | 0 | |
| Water | **0** | let the model infer 86.13 by difference |

**Why MSNF is zero.** `COMPONENT_FACTORS` gives MSNF `(8.3, 54.0)`, and that pair is purely
lactose-derived: standard MSNF is 52% lactose, and 0.52 × (16, 100) ≈ (8.3, 52). It is the
right factor for ordinary milk, where lactose is a fixed fraction of the milk solids. This
carton breaks that assumption — protein enrichment makes lactose only **34%** of its milk
solids, not 52%. Entering 12.7 g of MSNF would therefore overstate PAC by roughly 2.4 units
per 100 g of milk, about **11 PAC units** across a 1 kg batch: the calculator would tell you
the mix is soft when it is actually hard. So the lactose is entered explicitly and the
protein and minerals go to `other_solids`, which carries `(0, 0)` — correct, since protein's
molecular weight makes its freezing-point contribution negligible.

**Why trehalose.** The library has no lactose slot. Trehalose is `(20.0, 100.0)`; lactose is
about `(16, 100)`. Both are disaccharides at MW 342, so the PAC figure is exact, and the POD
overstatement is 4 units per 100 g of lactose — under 1 POD unit across a full batch.

**What this costs you.** With MSNF at zero, `msnf_pct` reads ~2% and the 10–12% window is
meaningless; read `nonfat_solids_pct` instead. `diagnose_recipe`'s lactose-sandiness check
also goes quiet, because it derives lactose from MSNF. Compute it by hand: it is
**3.3–3.4% of the water phase** in all three formulas, against a 10% threshold. That is a
genuine advantage of this carton — high milk solids with very little lactose — and it means
you could add milk powder later without the usual sandiness worry.

---

## Formula C · recommended

Half the added sugar of a conventional base, effective sweetness in range, no diagnostics
tripped except the ones the chocolate itself causes.

| | 1000 g | 700 g (Deluxe) |
|---|---|---|
| Protein chocolate milk | 468 g | 327 g |
| Cream 35% | 346 g | 242 g |
| Cocoa powder, unsweetened | 55 g | 38.5 g |
| Sucrose | 49 g | 34.3 g |
| Erythritol | 51 g | 35.7 g |
| Inulin | 30 g | 21 g |
| Fine salt | 0.5 g | 0.35 g |
| CMC | 1.0 g | 0.7 g |
| Kappa carrageenan | 0.1 g | 0.07 g |

| Metric | This recipe | Target |
|---|---|---|
| Milk fat | 13.0% | 12–15% |
| Total nonfat solids | 26.1% | 22–25% (see note) |
| Total solids | 39.0% | 37–42% |
| Water | 61.0% | 58–63% |
| Modeled sugars | 12.2% | 11–14% |
| Fiber | 2.4% | — |
| Lactose in water phase | 3.4% | <10% |
| **POD, modeled** | **92** | — |
| **POD, effective (est.)** | **114** | 110–120 |
| **PAC** | **249** | 245–255 |

Nonfat solids read 26.1% against a 22–25% window because cocoa powder is 81% nonfat solids
and inulin is another 3 points. That is what a 5.5% cocoa chocolate ice cream looks like; the
window was drawn for a plain base. Total solids, the metric that actually governs texture,
sits mid-range.

Added sugar is 4.9% of the mix, against 12–13% in a conventional formula. Energy lands near
170 kcal/100 g. Erythritol is 5.1% and inulin 3.0%, so a 100 g scoop carries ~5 g and ~3 g
respectively — modest enough that neither should cause trouble.

---

## Formula A · no added sugar at all

Keeps the carton's premise intact. The cost is sweetness: erythritol and inulin are poor
sweeteners per unit of PAC, so effective POD lands near **76** against a 110–120 window. This
is a genuinely dark, barely-sweet chocolate ice cream. At 6% cocoa that is a defensible
product, not a mistake — but taste the mix before you commit, and if you want it in range,
either move to Formula C or dose a sucralose-based tabletop sweetener to taste. Adjusting
sweetness with an intense sweetener is the one lever here that does not touch PAC at all.

| | 1000 g | 700 g |
|---|---|---|
| Protein chocolate milk | 468 g | 327 g |
| Cream 35% | 373 g | 261 g |
| Cocoa powder, unsweetened | 60 g | 42 g |
| Erythritol | 48 g | 33.6 g |
| Glycerol | 15 g | 10.5 g |
| Inulin | 35 g | 24.5 g |
| Fine salt | 0.5 g | 0.35 g |
| CMC | 1.0 g | 0.7 g |
| Kappa carrageenan | 0.1 g | 0.07 g |

Fat 14.0% · nonfat solids 23.4% · **total solids 37.4%** · water 62.6% · POD modeled 54,
effective ~76 · **PAC 251** · lactose in water 3.3%.

Fat runs at 14% rather than 13% deliberately: erythritol is so PAC-dense that you need very
little of it, which leaves total solids short. Fat is the cheapest way to buy the missing
solids back, and 37.4% is still only the bottom of the band. Glycerol at 1.5% carries 55 PAC
units on 15 g and keeps erythritol down; drop it if you dislike its warm, faintly sweet
finish, and add ~20 g erythritol plus ~5 g inulin instead. Note that a 150 g serving of this
one carries ~7 g erythritol and ~5 g inulin, which is enough fermentable material to bother
some people.

---

## Formula B · only sucrose and dextrose

If erythritol, glycerol and inulin are not in the cupboard.

| | 1000 g | 700 g |
|---|---|---|
| Protein chocolate milk | 463 g | 324 g |
| Cream 35% | 345 g | 242 g |
| Cocoa powder, unsweetened | 50 g | 35 g |
| Sucrose | 18 g | 12.6 g |
| Dextrose | 92 g | 64.4 g |
| Inulin | 30 g | 21 g |
| Fine salt | 0.5 g | 0.35 g |
| CMC | 1.0 g | 0.7 g |
| Kappa carrageenan | 0.1 g | 0.07 g |

Fat 12.9% · nonfat solids 26.6% · total solids 39.5% · water 60.5% · POD modeled 92,
effective ~114 · **PAC 250** · lactose in water 3.4%.

**This trips the dextrose diagnostic at 70% of the sugar blend, against the 50% ceiling, and
that is deliberate.** The ceiling exists to stop dextrose making a mix too sweet and too
soft. Here the sweetness budget is already spent by the carton's sweeteners, so the usual
reason to cap dextrose does not apply — but the other reason does: at 9.2% of the mix,
dextrose's low molecular weight means a softer, shorter, slightly stickier body than
Formula C's erythritol route. Drop inulin and it gets worse, because dextrose then has to
carry more PAC. If you have erythritol, prefer C.

---

## Kappa carrageenan is not a lambda substitute

The repo's presets dose lambda carrageenan at 0.3–0.4 g/kg. **Do not put kappa in at that
level.** Two things are different:

**Kappa gels with casein, and this mix is unusually full of it.** Kappa carrageenan forms
specific electrostatic complexes with κ-casein, and dairy calcium promotes gelation. At 4.1%
protein, most of it casein from skimmed milk plus milk protein concentrate, 0.3–0.4 g/kg of
kappa risks a mix that sets to a brittle gel, wheys off, or freezes into a puck too firm for
the machine to shave cleanly. The repository's own evidence note is explicit: calcium-containing
dairy can promote gel formation, this can create a base too firm to process, and kappa must
not be substituted one-for-one for lambda. Lambda's job in those presets — enriching melted
texture and holding protein in suspension — is a non-gelling job. Kappa cannot do it at the
same dose.

**Kappa needs heat.** Lambda hydrates at room temperature, which is why the no-cook preset
works. Kappa needs roughly 70–80 °C to dissolve and then sets on cooling. A cold-blended mix
with kappa in it gives you undissolved powder, not stabilizer.

So: **0.1 g/kg, and heat the mix.** That is a quarter of the lambda dose, enough to help with
protein suspension and melted body without building a real gel. If you would rather not heat
at all, leave kappa out entirely and run CMC alone at 1.2 g/kg — CMC hydrates cold and is the
better cold-process choice anyway.

**Count what is already in the carton.** The label lists E460 (cellulose), E466 (CMC) and
E407 (carrageenan) — an unspecified type, very likely kappa or a kappa/iota blend, since the
job in a drink is suspending cocoa. At 468 g of milk per kilo, a typical carton dose puts
somewhere around 0.1–0.25 g/kg of hydrocolloid into your mix before you weigh anything. The
formulas above therefore model only 0.11% gums against the 0.15–0.20% window, and that gap
is intentional: **do not chase the window**, because the calculator cannot see the carryover.
If the first batch comes out gummy or slow-melting, the carryover is the first thing to
suspect. E460 is insoluble microcrystalline cellulose and is not modeled here at all.

---

## Method

Heated, because kappa needs it and cocoa is much better for it.

**1. Preblend every powder.** Cocoa, sucrose (or erythritol), inulin, salt, CMC and kappa
into one bowl, whisked thoroughly. Cocoa and sugar are the carriers; a gum only clumps with
itself. Weigh CMC and kappa on a 0.01 g scale — 0.1 g cannot be spooned.

**2. Blend cold.** Chocolate milk and cream into the blender, lowest speed that forms a
vortex, rain the dry mix in, then 30 seconds on high.

**3. Heat to 80 °C, stirring,** and hold 5 minutes. This hydrates the kappa and CMC,
dissolves the erythritol, and blooms the cocoa — untoasted cocoa in a cold mix tastes flat
and dusty. Use **alkalized (Dutch-process) cocoa**, pH 7–8. Natural cocoa at pH 5.3–5.8
against 4.1% protein at 80 °C is asking for aggregation; the carton's E339 phosphate helps,
but there is no reason to lean on it.

**4. Homogenize hot** — full speed, one minute, while the fat is liquid. This is the step
that makes it smooth.

**5. Chill fast** to under 5 °C in an ice bath. Do not let it coast down in the fridge.

**6. Age 4–12 hours** below 4 °C. It will thicken and may set to a soft gel from the kappa.

**7. Break the gel** with a 10-second blend, pour into the tub to the MAX FILL line, level
the surface, and freeze flat at least 24 hours at −18 °C or colder.

**8. Spin on Ice Cream** (not Lite — total solids and fat are full-strength here). Powdery →
Re-spin with 1–2 tsp of the chocolate milk. Soupy → refreeze 20–30 minutes.

Judge sweetness warm. Cold suppresses it and frozen suppresses it further, so the aged mix
should taste slightly too sweet at room temperature.

---

## Adjustments

| Symptom | Fix |
|---|---|
| Too hard, needs several Re-spins | More erythritol (C, A) or dextrose (B), 5 g at a time. Both raise PAC far faster than POD. |
| Soupy out of the machine | Less erythritol/dextrose; or just refreeze 20–30 min. |
| Right texture, not sweet enough | A few drops of sucralose. It moves POD without touching PAC — use this before touching sugar. |
| Right texture, too sweet | Swap sucrose for erythritol at ~2.8 g sucrose per 1 g erythritol to hold PAC. |
| Gummy, elastic, slow melt | Carton carryover plus your additions. Drop CMC to 0.7 g and kappa to 0.05 g. |
| Watery, thin melt | Raise CMC toward 1.4 g. Leave kappa alone. |
| Brittle, snappy, weeps liquid after aging | Too much kappa. Halve it or remove it and go cold-process with CMC only. |
| Dry, dusty, drinks the saliva | Cocoa too high. Drop to 40 g and add ~10 g inulin to hold solids. |
| Chalky or gritty | Protein and cocoa fiber together. Homogenize harder at step 4 and lengthen aging. |
| Cold, minty-clean aftertaste | Erythritol's negative heat of solution. Shift some to sucrose (C) or glycerol (A). |
| Faintly bitter/metallic finish | Saccharin, concentrated by evaporation during the cook. Cover the pot, or top back up to weight after step 3. |

---

## What the calculator cannot see

Read the numbers above as a starting point, not a measurement. Five things are estimated:

1. **Density 1.045 g/ml.** Every component scales with it. Weigh a full carton — a 1 L pack
   should net about 1045 g — and rescale if it is off.
2. **Ash ≈ 1.0 g/100 ml.** Inferred from the skimmed-milk fraction plus the mineral load a
   milk-protein concentrate carries, plus E339. It only affects total solids, by under 0.5
   points at these doses.
3. **Effective POD.** The +22 units attributed to saccharin and sucralose assume they replace
   about 5 g of sucrose per 100 ml, which is what AH's ordinary chocolate milk carries above
   its lactose. If the carton tastes more or less sweet than that to you, the effective POD
   figures move with it. This is the softest number on the page, and it is the one that
   decides whether the ice cream tastes right.
4. **Salt and milk minerals.** Dissolved milk salts genuinely depress freezing point — real
   milk freezes at −0.52 °C, while this engine's MSNF factor accounts for only about
   −0.29 °C of that, because the factor is lactose-derived. The repo's own milk and cream
   entries carry no salt component either, so the carton is modeled on the same basis and the
   comparison holds. But it means PAC is systematically understated for every dairy formula
   here, this one included — perhaps 5–10 units. It biases toward a softer result than
   predicted, which is the safer direction for a machine that shaves a puck.
5. **Stabilizer carryover.** Unquantifiable from the label. See above.

The lactose figure, by contrast, is solid: it is a declared label value, and at 3.4% of the
water phase it is nowhere near trouble.
