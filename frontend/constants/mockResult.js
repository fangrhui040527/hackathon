export const MOCK_RESULT = {
  product: 'Oreo Cookies',
  type: 'Ultra-Processed Snack',
  servingSize: '3 cookies (34 g)',
  nutrition: [
    { label: 'Calories', value: '160 kcal' },
    { label: 'Sugar',    value: '21 g'     },
    { label: 'Fat',      value: '7 g'      },
    { label: 'Sat. Fat', value: '3.5 g'    },
    { label: 'Sodium',   value: '135 mg'   },
    { label: 'Carbs',    value: '25 g'     },
    { label: 'Protein',  value: '< 1 g'    },
    { label: 'Fibre',    value: '0.5 g'    },
  ],
  funFacts: [
    'Oreos have been sold since 1912 — over 110 years old, yet they still contain no real vanilla extract.',
    'The cream filling is made entirely from vegetable shortening and sugar. There is no cream or dairy in it.',
    'Oreo is the world\'s best-selling cookie with over 40 billion produced annually across 100+ countries.',
    'Studies show the sugar–fat–salt ratio in Oreos activates the same dopamine reward pathways as habit-forming substances.',
    'Nabisco holds 40+ patents covering the Oreo\'s design, manufacturing process, and proprietary embossing pattern.',
  ],
  conclusion: {
    verdict: 'avoid',
    summary:
      'Oreo cookies are ultra-processed, high in refined sugar and saturated fat, ' +
      'with synthetic additives offering no meaningful nutritional value. Regular ' +
      'consumption poses measurable risk across metabolic, cardiovascular, and ' +
      'digestive health — particularly concerning for individuals with existing ' +
      'conditions. Occasional indulgence is low risk for healthy adults, but these ' +
      'should not be a dietary staple.',
    ok_for: [
      'Occasional rare treat',
      'Healthy adults with no metabolic issues',
      'Post-workout glycogen top-up (small amount)',
    ],
    avoid_if: [
      'Diabetes or insulin resistance',
      'High blood pressure',
      'Heart disease or high cholesterol',
      'Weight loss or calorie-deficit goals',
      'Gut health concerns or IBS',
    ],
    flags: ['Ultra-processed', 'High sugar', 'Synthetic additives', 'Low nutritional value'],
    confidence: 89,
  },
  agentOutputs: [
    {
      agentId: 1,
      verdict: 'avoid',
      summary:
        'Each serving (3 cookies, 34 g) contains 21 g of sugar — 42 % of the ' +
        'recommended daily limit. Chronic intake at this level elevates insulin ' +
        'resistance, triglyceride levels, and systolic blood pressure. Patients ' +
        'with diabetes, metabolic syndrome, or hypertension should treat this as a ' +
        'red-flag food and limit consumption strictly.',
      flags: ['21 g sugar/serving', 'High glycaemic index', 'Saturated fat 3.5 g', 'Raises triglycerides'],
      confidence: 91,
      considered_health_note: true,
    },
    {
      agentId: 2,
      verdict: 'caution',
      summary:
        'Oreos deliver 160 kcal per 3-cookie serving almost entirely from refined ' +
        'carbohydrates and fat, with negligible protein (< 1 g) and minimal fibre ' +
        '(0.5 g). The calorie-to-nutrient density ratio is extremely poor. They ' +
        'will not support satiety or micronutrient needs. Suitable only as a very ' +
        'occasional treat within a well-balanced diet.',
      flags: ['Empty calories', '< 1 g protein', '0.5 g fibre', '135 mg sodium'],
      confidence: 88,
      considered_health_note: false,
    },
    {
      agentId: 3,
      verdict: 'avoid',
      summary:
        'Ingredient analysis reveals vanillin (synthetic flavour), soy lecithin ' +
        '(emulsifier), and TBHQ traces (preservative). High-temperature baking of ' +
        'starchy dough generates measurable acrylamide — a probable human ' +
        'carcinogen per IARC. The palm oil fraction contains elevated levels of ' +
        'glycidyl esters, raising additional safety concerns with frequent use.',
      flags: ['Synthetic vanillin', 'TBHQ preservative', 'Acrylamide risk', 'Glycidyl esters'],
      confidence: 84,
      considered_health_note: false,
    },
    {
      agentId: 4,
      verdict: 'caution',
      summary:
        'Simple carbohydrates in Oreos cause a rapid glucose spike (GI ≈ 71) ' +
        'followed by a sharp crash — counterproductive for sustained athletic ' +
        'output or body composition goals. A small amount immediately post-workout ' +
        'could aid glycogen replenishment, but superior options exist. Avoid ' +
        'pre-workout entirely as they will impair endurance and focus.',
      flags: ['GI ≈ 71', 'No protein for recovery', 'Post-workout only at best', 'Poor body-comp food'],
      confidence: 77,
      considered_health_note: false,
    },
    {
      agentId: 5,
      verdict: 'avoid',
      summary:
        'Epidemiological data consistently links ultra-processed food consumption ' +
        '(NOVA group 4, which Oreos fall into) with a 12 % higher all-cause ' +
        'mortality risk, gut microbiome dysbiosis, and accelerated cellular ageing ' +
        'markers. The reward-pathway engagement of the sugar–fat–salt combination ' +
        'also elevates compulsive eating risk. From a preventive-health standpoint, ' +
        'these should be a genuine rarity in the diet.',
      flags: ['NOVA group 4', 'Microbiome disruption', 'Compulsive-eating risk', 'Longevity concern'],
      confidence: 86,
      considered_health_note: true,
    },
    {
      agentId: 6,
      verdict: 'caution',
      summary:
        'Oreo cookies contain no explicitly Haram ingredients, but the source of ' +
        'mono- and diglycerides and natural flavors is unverified — they may be ' +
        'animal-derived. Oreos are not certified Halal or Kosher in all markets. ' +
        'They are not vegan due to potential cross-contact with milk during ' +
        'manufacturing ("may contain milk" warning).',
      flags: ['Halal status uncertain', 'Not certified vegan', 'Cross-contact risk', 'Verify local certification'],
      confidence: 74,
      considered_health_note: false,
    },
  ],
};
