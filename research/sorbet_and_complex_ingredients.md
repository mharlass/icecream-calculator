# Sorbet, fruit, and chocolate formulation: evidence and implementation note

## Scope and evidence convention

This note supports adding sorbet bases and richer ingredient-entry cards to the Ice
Cream Formula Calculator. It separates:

- **Measured composition:** data that can be entered and added arithmetically.
- **Published mechanism:** evidence about freezing, rheology, or texture.
- **Practical formulation envelope:** a professional starting range, not a universal
  optimum.
- **Implementation assumption:** a choice that still needs recipe and machine testing.

The distinction matters here. Fruit composition changes with cultivar, maturity, season,
and processing. USDA Foundation Foods deliberately exposes sample-level variability for
this reason.[1] A refractometer reading adds useful lot-specific information, but it does
not fully identify sugar composition or total dry matter.[2]

## Main recommendation

Do not implement “sorbet” as dairy ice cream with fat and milk solids-not-fat (MSNF)
targets set to zero. Implement three separate concepts:

1. A **fruit sorbet profile**, where water, total solids, sugar composition, relative
   sweetness (POD), and freezing-point depression (PAC) are primary. Fat and MSNF should
   read “not applicable” rather than appear as failed targets.
2. A **named fruit starting base**, initially strawberry or another explicitly sourced
   fruit. Do not invent a universal “fruit purée” composition.
3. A later, distinct **chocolate sorbet profile**. Chocolate sorbet contains cocoa butter
   and needs substantially different fat, solids, POD, and PAC ranges from fruit sorbet.

The current inverse solver is dairy-specific. It solves mass, fat, MSNF, POD, and PAC
using exactly five free ingredients. In a fruit sorbet, fat and MSNF contributions are
normally zero across all candidate ingredients, so those equation rows do not identify
ingredient weights and the matrix becomes singular. A sorbet solver needs a different
contract, for example mass, total solids, POD, and PAC while fruit and stabilizer
quantities are locked. The number of free rows must match that contract.

## 1. Sorbet targets and starting bases

### What is well supported

- Sorbet hardness cannot be predicted from total sugar alone. Freezing-point depression
  depends strongly on the amount and molecular size of individual soluble sugars.
  Fructose and glucose contribute more freezing-point depression per gram than sucrose
  because their molecular masses are lower.[3,4]
- Studies of apple, pear, peach, and citrus juices model freezing behavior using
  sugar composition, and for citrus, sugar-acid composition and non-ideal
  solute-solvent interactions.[5,6] Treating every fruit sugar as sucrose is therefore
  an approximation.
- Fruit pulp is not simply sugar and water. Pectin, suspended particles, and processing
  change viscosity and freezing behavior. In passion-fruit pulp, sucrose and pectin
  interacted to alter rheology and movement of the freezing front.[7]
- There is no source located here that validates one PAC/POD window specifically for
  Ninja CREAMi or Pacojet fruit sorbet. Machine-specific targets should be presented as
  experimental until tested.

### Practical fruit-sorbet envelope

An Italian professional gelato source presents the following broad fruit-sorbet
envelope: 29-33% total solids, 28-32% total sugars, 67-71% water, POD 22-27, and PAC
27-34 on a per-100-g scale.[8] In this application's per-1,000-g convention, the last two
become approximately **POD 220-270** and **PAC 270-340**.

These are useful **display and warning ranges**, not hard solver targets:

| Metric | Provisional fruit-sorbet display range | How to present it |
|---|---:|---|
| Total solids | 29-33% | Practical starting envelope |
| Water | 67-71% | The complement of total solids when mass is fully accounted for |
| Total sugars | 28-32% | Include natural fruit sugars and added sugars |
| POD | 220-270 | Broad sweetness envelope; fruit acidity changes perceived balance |
| PAC | 270-340 | Broad hardness envelope; serving temperature and machine matter |
| Fat | Not a target | Show the measured trace value only |
| MSNF | Not applicable | Hide or mark N/A |
| Stabilizer | No universal target established here | Follow the selected gum and supplier/process guidance |

This broad range should not be silently narrowed into separate “CREAMi/Pacojet” and
“churned” sorbet profiles. The current dairy offset between those profiles has not been
validated for fruit sorbet. The better first release is one clearly labelled
**experimental fruit sorbet** profile with editable POD and PAC goals, followed by
machine-specific calibration from tested recipes.

There is also a genuine sweetness disagreement between professional approaches.
Underbelly's high-fruit strawberry formula reports POD 144, PAC 318, and 24.7% total
solids, while explicitly criticizing the sweetness of conventional POD-above-200
sorbets.[21] The comment discussion under that formula disputes its reported solids
arithmetic, so the app should recompute every metric rather than copying the analysis
values.[21]

For this calculator, whose dairy profiles also favor restrained POD, the most useful
initial profile is therefore:

| Metric | Recommended initial app range | Basis |
|---|---:|---|
| Total solids | 25-33% | Spans the reported high-fruit example and the professional envelope |
| Water | 67-75% | Complementary practical display range |
| POD | 140-200 | Lower-sweetness product choice, not a consensus standard |
| PAC | 300-340 | Contains the high-fruit example and the upper professional envelope |

Use one profile for both methods until it is tested. If the interface must provide
method-specific PAC bands immediately, **CREAMi/Pacojet 310-340** and **churned 300-325**
are a transparent provisional partition of the common range. Keeping POD 140-200 for
both is more defensible because the machine does not determine desired sweetness. These
two PAC bands are an **implementation assumption**, not published machine-specific
evidence.

### Starting base

A generic base cannot be numerically balanced until the fruit is known. Two defensible
interface choices are:

- Require the user to choose or create a fruit ingredient before loading a sorbet
  scaffold.
- Ship one named, cited starter such as strawberry, and state that replacing the fruit
  requires rebalancing.

Professional and research recipes illustrate why a fixed generic ratio is unsafe. A
Valrhona/Sosa strawberry recipe uses sweetened strawberry purée, dextrose, glucose
powder, water, citric acid, guar, and locust bean gum.[9] A published peach-sorbet
control instead used 63% peach purée, 15.99% sucrose, 21% water, and 0.01% citric
acid.[10] These are examples of complete formulations, not proof that either is optimal
for the user's machine.

For a practical seed that fits the lower-sweetness profile, Underbelly publishes
these strawberry formula line items:[21]

| Ingredient | Grams |
|---|---:|
| Strawberries, specified at 8-9 °Brix | 750 |
| Water | 52 |
| Dextrose | 42 |
| Atomized glucose DE40 | 65 |
| Trehalose | 40 |
| Erythritol | 20 |
| Inulin | 27 |
| CMC | 2 |
| Guar gum | 1 |
| Lambda carrageenan | 1 |
| Salt | 1 |
| **Line-item total** | **1,001** |

The published quantities sum to 1,001 g even though the source presents the recipe as
a 1,000 g formulation. The app uses 51 g rather than 52 g water to normalize the
starter to exactly 1,000 g while preserving every functional ingredient quantity.

This is a culinary formulation source, not a peer-reviewed CREAMi/Pacojet validation.
It was designed for a conventional ice-cream machine and a serving temperature of
approximately -12 to -14 °C.[21] It is nevertheless a better seed than a made-up generic
fruit because its fruit quality assumption and complete formula are explicit.

The current USDA Foundation Foods April 2026 record for raw strawberries (FDC ID
2346409) reports, per 100 g, 90.8 g water, 0.22 g fat, 2.24 g glucose, 2.62 g fructose,
0 g sucrose, 0.641 g protein, 0.345 g ash, and 7.96 g carbohydrate by difference.[22]
The analyzed sugars sum to 4.86 g, appreciably below the seed recipe's 8-9 °Brix fruit
specification. Preserve the USDA values as a sourced average preset, but do not pretend
they describe an 8-9 °Brix batch. Ask for a measured Brix or clearly label any
sugar-and-water adjustment as an estimate.

That Foundation record does not report total dietary fiber. For an app ingredient preset
that must close to exactly 100 g, retain the reported water, fat, and individual sugars and
assign the 4.12 g remainder to `other_solids`. This remainder contains all unmodeled
protein, ash, fiber and other carbohydrate, organic acids, and rounding residue. It must
not be presented as measured fiber. Reconstructing it instead from the rounded USDA
proximate fields gives 4.086 g and a total of 99.966 g, with the 0.034 g difference caused
by rounding.

### Chocolate sorbet is a separate profile

Callebaut's own technical compendium specifies a practical chocolate-sorbet envelope of
5-8% fat, 4.5-5.5% dry cocoa solids, 26-28% total sugar, 37-40% total solids, PAC
265-270, and POD 170-190.[11] Its worked chocolate-sorbet recipes are consistent with
roughly 39-40% total solids and PAC near 265-273.[11]

Those values apply to water-based **chocolate** formulations containing cocoa butter.
They must not become the fruit-sorbet targets. If chocolate sorbet is added later, it
also needs a dry-cocoa-solids metric that the current engine does not calculate.

## 2. Fruit, purée, and juice ingredient card

### Minimum honest inputs

Use two entry levels. A short card should remain usable from a package label. An
advanced section should support formulation-quality data.

| Input per 100 g | Required? | Why it matters |
|---|---|---|
| Name and form: whole/purée/juice/concentrate/dried | Yes | Straining, concentration, and drying change water and insoluble solids |
| Water | Yes, direct or inferred | Determines ice-forming water and total solids |
| Total sugars | Yes | Basic mass balance and sweetness/freezing contribution |
| Sucrose, glucose, and fructose split | Required for accurate POD/PAC; otherwise an explicit estimate | Mono- and disaccharides have different POD/PAC |
| Fat | Yes, default 0 | Needed for avocado, coconut, cocoa-fruit products, and correct total solids |
| Fibre | Yes when known | Contributes solids and can alter viscosity/body |
| Protein | When known | Contributes solids and can affect structure |
| Starch/other carbohydrate and ash | When known, or residual “other solids” | Completes the mass balance |
| °Brix | Optional lot measurement | Useful quality-control signal, not a direct sugar assay |
| pH and/or titratable acidity | Optional advanced metadata | Helps interpret tartness and hydrocolloid or dairy compatibility |
| Alcohol | When present | Strong freezing-point contribution |
| Source/note | Yes for presets | Preserve whether values came from USDA, a supplier sheet, a label, or an estimate |

USDA Foundation Foods is a sensible source for built-in raw-fruit compositions because
it can provide water, fat, protein, ash, fibre, and individual glucose, fructose, and
sucrose values, together with sampling metadata.[1] Store a dated snapshot and source
identifier rather than calling an API from the browser at recipe time. The user should
still be able to override the preset for a commercial purée or the fruit actually used.

### Derived mapping into the present engine

For an initial implementation:

| Entered value | Current component |
|---|---|
| Water | `water` |
| Fat | `fat` |
| Sucrose | `sucrose` |
| Glucose | `dextrose` |
| Fructose | `fructose` |
| Fibre | `fiber`, included in nonfat and total solids |
| Protein, starch, pectin, ash, and insoluble pulp | `other_solids` |
| Alcohol | `alcohol` |

This mapping gives correct component mass accounting and applies the existing
sugar-specific POD/PAC coefficients. It does **not** turn fibre or pectin into a
quantitative texture prediction.

Organic acids expose another limitation. They count as solids and influence flavor,
and fruit-juice freezing models can require sugar-acid composition.[6] Mapping all acid
to `other_solids` gives it zero PAC in the current engine, which can understate the
freezing contribution of acidic fruit. Do not silently assign a universal “citric-acid
PAC” without validating the convention. Record acidity as metadata now, disclose the
omission, and consider acid-specific components in a later, tested model.

### How to use °Brix

The EU refractometric definition of Brix is the mass percentage of a sucrose solution
with the same refractive index as the sample.[2] In fruit products, the reading therefore
represents sucrose-equivalent **soluble residue**, not grams of sugar and not total
solids. Acids and other dissolved material contribute to the reading, while insoluble
fibre does not.

Consequently:

- Do not map °Brix directly to `sucrose`.
- Do not compute water as `100 - Brix` for a purée.
- Use measured °Brix to flag that the current fruit lot differs from the stored preset.
- A future adjustment tool may scale the preset's sugar contribution while holding
  measured or database non-sugar solids fixed, but it must label this as an estimate.

## 3. Cocoa powder and chocolate ingredient cards

“70% chocolate” is insufficient composition data. Valrhona explains that cocoa
percentage combines cocoa nib material and cocoa butter, and that two chocolates with
the same cocoa percentage can contain different proportions of each.[12] A specific
Callebaut 70.5% dark couverture, for example, declares 38.9% fat and 26.3% sugars.[13]

### Chocolate or couverture

Ask for:

- product type: dark, milk, white, couverture, or cocoa mass;
- fat;
- sugars, with sucrose as the default only when supported by the ingredient list;
- water/moisture, if available;
- total carbohydrate, fibre, protein, and salt;
- total cocoa solids and, if the supplier provides it, nonfat dry cocoa solids;
- milk solids or lactose for milk and white chocolate;
- lecithin/emulsifier presence as metadata;
- whether it is fully melted into the base or used as pieces/ripples.

Map fat to `fat`, verified sugar to its sugar component, moisture to `water`, dairy
solids to `msnf` only when their composition is actually known, and the remaining cocoa
material to `other_solids`. Cocoa butter and milk fat have different melting behavior,
so “total fat” remains useful arithmetic but is not a complete texture model.

### Cocoa powder

Ask for fat, moisture, sugars, fibre, protein, salt/ash if available, and whether the
powder is natural or alkalized. Supplier pH is useful metadata because alkalization and
pH affect flavor and compatibility. Barry Callebaut, for example, publishes an alkalized
cocoa powder with a pH specification of approximately 7.2-7.7.[14]

### Dispersed ingredient versus mix-in

The calculator assumes every declared component is uniformly dispersed through the
base. Fruit pieces, chocolate chips, and ripples form separate frozen domains and should
be marked as **mix-ins**. Their nutrition can be reported, but their water and PAC should
not be presented as though they guarantee the same base texture as a dissolved or
puréed ingredient.

## 4. Fibre and texture: what can be represented honestly

Published work supports a real effect of fibre source and form, but not a universal
grams-to-texture conversion. In model ice cream, insoluble fibre increased viscosity and
shear-thinning through hydrated cellulose/hemicellulose networks. Effects depended on
plant source and the soluble-to-insoluble ratio.[15] Pectin concentration, sucrose,
acidity, and processing interact in fruit-pulp rheology and freezing.[7]

The separate `fiber` component and residual `other_solids` bucket can honestly answer:

- how much fibre mass was added;
- how it changes total solids and water by mass.

It cannot honestly predict:

- water-binding capacity;
- serum-phase viscosity;
- iciness or recrystallization control;
- gumminess, grittiness, or particle perception;
- the effect of soluble versus insoluble fibre, particle size, homogenization, or heat.

Recommended first implementation: retain fibre as a separately displayed input and
metric, and include its mass in nonfat and total solids. Add a qualitative note that
fibre affects body but is not part of the solver. Do not create a “texture score” from
total fibre grams.

## 5. Are custom ingredients saved in the current Shinylive app?

**No, not across a reload.** In the current app, `library_state` is a
`reactive.Value(default_library())` created inside `server()`. Added ingredients modify
that in-memory reactive value. Official Shiny documentation states that each browser
session has its own state and that the session ends when the user navigates away, closes
the window, or loses the connection.[16] Shinylive runs the app entirely in the browser
and exports it for a static web server. It does not add a database.[17]

Therefore, a custom ingredient currently:

- remains available during the live tab/session;
- disappears on refresh or reopening the app;
- is not shared with another browser/device or another user;
- is not written back to GitHub Pages or the repository.

Pyodide's default browser filesystem is in-memory and is lost on reload unless a
persistent filesystem is explicitly mounted and synchronized.[18] The simplest future
option would be explicit JSON storage in browser `localStorage`, which persists for the
same origin across normal browser sessions.[19] It is still browser- and origin-local,
may be cleared or blocked, and private browsing clears it. Portable JSON
export/import would be a useful companion, but persistence was not implemented as part
of this research task.

## Implementation sequence suggested by the evidence

1. Add the fruit/purée/juice card and the necessary pure-model constructors and tests.
   Preserve provenance and explicitly mark estimated sugar splits.
2. Add one named fruit-sorbet starter plus the broad experimental fruit-sorbet display
   profile. Hide dairy targets for that recipe family.
3. Replace or disable the five-variable dairy solver for sorbet until a sorbet-specific
   equation set is tested.
4. Validate the named starter in the intended machine and at the actual freezer
   temperature before narrowing POD/PAC ranges.
5. Add chocolate/cocoa cards. Add a separate chocolate-sorbet profile only when dry
   cocoa solids can be calculated.
6. Keep fibre and acidity visible as composition/metadata, with explicit model
   limitations. Do not imply a deterministic texture prediction.

## Evidence gaps to disclose

- No reviewed source located here validates a CREAMi- or Pacojet-specific fruit-sorbet
  target window.
- Practical sorbet targets vary with serving temperature, overrun, fruit, acidity,
  soluble/insoluble solids, and the sugar blend.
- USDA values describe sampled foods, not the exact fruit or commercial purée in the
  user's kitchen.
- Nutrition labels usually report total sugars, not the sucrose/glucose/fructose split.
  The EU mandatory declaration also separates carbohydrate, sugars, protein, fat, and
  salt, while fibre is optional.[20]
- Brix is not a complete substitute for composition analysis.
- Existing component arithmetic cannot quantify organic-acid PAC, cocoa-butter
  crystallization, fibre water-binding, or particulate texture.

## Sources

1. USDA FoodData Central. **Foundation Foods Documentation**.
   <https://fdc.nal.usda.gov/Foundation_Foods_Documentation/>
2. European Commission. **Implementing Regulation (EU) No 974/2014: determination of
   Brix by refractometry**.
   <https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32014R0974>
3. Clarke C. **Controlling the hardness of ice cream, gelato and similar frozen
   desserts**. *Food Science and Technology*. 2021.
   <https://doi.org/10.1002/fsat.3510_3.x>
4. Young FE, Jones FT. **Effects on freezing point of carbohydrates commonly used in
   frozen desserts**. *Journal of Dairy Science*. 1983.
   <https://doi.org/10.3168/jds.S0022-0302(83)82112-2>
5. Auleda JM, Raventós M, Sánchez J, Hernández E. **Estimation of the freezing point of
   concentrated fruit juices for application in freeze concentration**. *Journal of
   Food Engineering*. 2011.
   <https://doi.org/10.1016/j.jfoodeng.2011.02.035>
6. Chen CS, Nguyen TK, Braddock RJ. **Relationship between freezing point depression
   and solute composition of fruit juice systems**. *Journal of Food Science*. 1990.
   <https://doi.org/10.1111/j.1365-2621.1990.tb06815.x>
7. **Effects of added sucrose and pectin on the rheological behavior and freezing
   kinetics of passion fruit pulp studied by response surface methodology**.
   <https://pmc.ncbi.nlm.nih.gov/articles/PMC4444898/>
8. Italian Gelato. **The art of crafting gelato: balancing the mixture for perfection**.
   Professional formulation guidance, not a controlled study.
   <https://www.italiangelato.info/artisan-gelato/articles/the-art-of-crafting-gelato-balancing-the-mixture-for-perfection.kl>
9. Valrhona/Sosa. **Strawberry Sorbet**.
   <https://www.valrhona.us/our-recipes/recipes/all-our-recipes/strawberry-sorbet>
10. Petkova N, et al. **Characterization of fruit sorbet matrices with added value from
    Zizyphus jujuba and Stevia rebaudiana**.
    <https://doi.org/10.3390/foods11182748>
11. Callebaut. **The A-Z for Perfect Chocolate Ice Cream**, pp. 14, 79-82.
    <https://www.callebaut.com/sites/default/files/14-9375%20CAL%20Ice%20cream%20compendium%20EN_v11_singlepage_LR_0.pdf>
12. Valrhona. **Dark chocolate: what cocoa percentage means**.
    <https://www.valrhona.com/en/l-ecole-valrhona/discover-l-ecole-valrhona/chocolate-terminology/dark-chocolate>
13. Callebaut. **70-30-38 dark chocolate product specification**.
    <https://shop.callebaut.com/en-de/dark-chocolate-couverture-drops-70-30-38/70-30-38-E0-D94.html>
14. Barry Callebaut. **D102B cocoa powder product specification**.
    <https://www.barry-callebaut.com/en-IL/manufacturers/products/barry-callebaut-d102b/DCP-10B102-789>
15. Soukoulis C, Lebesi D, Tzia C. **Enrichment of ice cream with dietary fibre:
    effects on rheological properties, ice crystallisation and glass transition
    phenomena**. *Food Chemistry*. 2009.
    <https://doi.org/10.1016/j.foodchem.2008.12.070>
16. Posit. **Shiny for Python: session lifecycle**.
    <https://shiny.posit.co/py/docs/opentelemetry.html#session-lifecycle>
17. Posit. **Shinylive: run Shiny applications in the browser and host on a static
    server**.
    <https://posit-dev.github.io/r-shinylive/>
18. Pyodide. **File-system persistence and IDBFS**.
    <https://pyodide.org/en/stable/usage/faq.html#why-changes-made-to-indexeddb-don-t-persist>
19. MDN. **Window: localStorage property**.
    <https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage>
20. European Union. **Regulation (EU) No 1169/2011 on food information to consumers**.
    <https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32011R1169>
21. Underbelly. **Sample Sorbet Recipe: Strawberry**. Practical culinary formulation
    and analysis.
    <https://under-belly.org/sample-sorbet-recipe/>
22. USDA FoodData Central. **Foundation Foods, April 2026 JSON release**. Strawberry
    record FDC ID 2346409.
    <https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_json_2026-04-30.zip>
