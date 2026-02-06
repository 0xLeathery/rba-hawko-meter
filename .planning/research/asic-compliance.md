# ASIC Compliance Research for Hawk-O-Meter Dashboard

## Research Date: February 2026

## Table of Contents

1. [Regulatory Framework Overview](#1-regulatory-framework-overview)
2. [Key Definitions: Information vs Advice](#2-key-definitions-information-vs-advice)
3. [Is the Hawk-O-Meter "Financial Product Advice"?](#3-is-the-hawk-o-meter-financial-product-advice)
4. [Mortgage Calculator Analysis](#4-mortgage-calculator-analysis)
5. [Safe vs Risky Language](#5-safe-vs-risky-language)
6. [Disclaimer Requirements and Examples](#6-disclaimer-requirements-and-examples)
7. [Competitor Disclaimer Analysis](#7-competitor-disclaimer-analysis)
8. [Data Attribution Requirements](#8-data-attribution-requirements)
9. [Australian Consumer Law Implications](#9-australian-consumer-law-implications)
10. [Consequences of Non-Compliance](#10-consequences-of-non-compliance)
11. [Compliance Checklist for Hawk-O-Meter](#11-compliance-checklist-for-hawk-o-meter)

---

## 1. Regulatory Framework Overview

### Governing Legislation

- **Corporations Act 2001 (Cth)**, Chapter 7 (Financial Services and Markets)
- **ASIC Regulatory Guide 244** (RG 244): Giving information, general advice and scaled advice
- **ASIC Regulatory Guide 175** (RG 175): Licensing: Financial product advisers -- Conduct and disclosure
- **ASIC Regulatory Guide 36** (RG 36): Licensing: Financial product advice and dealing
- **ASIC Information Sheet 269** (INFO 269): Discussing financial products and services online
- **ASIC Corporations (General Advice Warning) Instrument 2015/540**
- **Australian Consumer Law** (Schedule 2 of the Competition and Consumer Act 2010), Section 18

### Key Regulatory Bodies

- **ASIC** (Australian Securities and Investments Commission): Regulates financial services, markets, and consumer credit conduct
- **ACCC** (Australian Competition and Consumer Commission): Enforces Australian Consumer Law provisions on misleading and deceptive conduct

### AFS Licensing Requirement

Section 911A of the Corporations Act requires anyone who carries on a business of providing financial services to hold an Australian Financial Services (AFS) licence, unless exempt. Financial services include providing financial product advice.

---

## 2. Key Definitions: Information vs Advice

### The Three-Tier Hierarchy

ASIC RG 244 establishes a critical three-tier hierarchy:

#### Tier 1: Factual Information (NOT financial product advice)

> Factual information is **objectively ascertainable information, the truth or accuracy of which cannot reasonably be questioned**.

Providing factual information does NOT constitute financial product advice and does NOT require an AFS licence. Examples include:

- Stating the current RBA cash rate
- Reporting that futures market pricing implies a specific probability
- Describing how monetary policy works
- Explaining what economic indicators measure
- Presenting historical data and statistics

**Key test**: The information must be objectively verifiable and must not include any recommendation or statement of opinion intended to influence a financial decision.

#### Tier 2: General Advice (financial product advice, but NOT personal)

> General advice is financial product advice that is **not personal advice**. It includes recommendations or statements of opinion about financial products that do not take into account the individual's objectives, financial situation, or needs.

General advice DOES require an AFS licence and triggers the general advice warning obligation under s949A of the Corporations Act.

#### Tier 3: Personal Advice (financial product advice that IS personal)

> Personal advice is financial product advice given in circumstances where the provider has **considered one or more of the person's objectives, financial situation and needs**, or where **a reasonable person might expect the provider to have considered** one or more of those matters.

Per the High Court decision in *Westpac Securities Administration Ltd v ASIC* [2021] HCA 3:

- "Might expect" sets a threshold of **reasonable possibility, not reasonable probability** -- a notably broad test
- "Considered" means simply to **"take account of" or "give attention to"** -- a low threshold
- A single general advice disclaimer at the start of a communication **cannot override** the advice's personal character
- Personal advice need not address ALL of a client's circumstances; considering **at least one** aspect suffices

### The Critical Legal Definition: Section 766B Corporations Act

**Financial product advice** is defined as:

> A **recommendation** or a **statement of opinion**, or a report of either of those things, that:
> (a) is **intended to influence** a person in making a decision in relation to a particular financial product or class of financial products; or
> (b) **could reasonably be regarded** as being intended to have such an influence.

Key elements:
- **Recommendation** = "to commend or urge a particular course of action"
- **Opinion** = "an expression of a belief, view, estimation or judgment"
- The intent test is BOTH subjective ("intended to influence") AND objective ("could reasonably be regarded as")

---

## 3. Is the Hawk-O-Meter "Financial Product Advice"?

### Analysis: The Hawk Score Gauge (0-100)

**Strong argument for "factual information" classification:**

The Hawk-O-Meter aggregates publicly available economic data (CPI, employment, GDP, etc.) and derives a normalised composite score. If the methodology is:

1. **Transparently documented** (users can see how the score is calculated)
2. **Based on objectively ascertainable data** (official ABS/RBA statistics)
3. **Not accompanied by recommendations** (no "you should fix your rate" language)
4. **Framed as market-derived information** (not editorial opinion)

Then it likely falls within the "factual information" tier and does NOT constitute financial product advice.

**Risk factors that could push it toward "general advice":**

- Using language like "the RBA **will** raise rates" (opinion/prediction)
- Suggesting users take action based on the score
- Colour-coding that implies "good" or "bad" (red = danger, green = safe)
- Any language that could be interpreted as a recommendation about financial products (mortgages, savings accounts, bonds)

### Comparison: ASX RBA Rate Tracker

The ASX publishes an almost identical tool -- the **RBA Rate Tracker** -- which shows market-implied probabilities of rate changes derived from ASX 30 Day Interbank Cash Rate Futures. The ASX classifies this as **indicative information, not investment advice**, with the disclaimer:

> *"This information is indicative only. It is not investment advice and readers should seek their own professional advice."*

The Hawk-O-Meter is analogous but uses a broader set of indicators rather than futures pricing alone. If the ASX -- a major licensed financial market operator -- classifies similar output as "indicative information", the Hawk-O-Meter has a strong precedent for the same classification.

### Comparison: RBA Rate Watch (rbaratewatch.com)

This independent website shows market-implied rate probabilities and uses:

> *"For informational purposes only. This is not financial advice."*
> *"Based on financial market data. Not a forecast, recommendation, or financial advice."*

### Key Safeguards for the Hawk-O-Meter

To remain in the "factual information" tier:

1. **Use "Market Expectation" not "Prediction"** -- already planned (good)
2. **Never recommend specific financial products** or actions
3. **Frame the score as a data aggregation tool**, not a forecast
4. **Traffic light colours**: Use carefully -- frame as "hawkish" (red) vs "dovish" (blue/green), NOT as "danger" vs "safe". The colours should describe RBA posture, not user risk.
5. **Disclose methodology transparently** so users understand it is a mathematical derivation, not an opinion
6. **Include prominent "General Information Only" disclaimer** -- already planned (good)

---

## 4. Mortgage Calculator Analysis

### Does a "rate change impact on repayments" calculator cross into personal advice?

**Short answer: Almost certainly NO, if properly disclaimed.**

### Analysis

A mortgage calculator where users enter their own loan details (amount, term, rate) and see how repayments change under different rate scenarios is a **mathematical computation tool**, not financial product advice, because:

1. **It does not recommend any product** -- it performs arithmetic
2. **It does not consider the user's broader financial situation** -- it processes only the numbers they enter
3. **It does not suggest any course of action** -- it shows "if X, then Y"
4. **There is massive industry precedent** -- ASIC itself runs a mortgage calculator on MoneySmart.gov.au

### Industry Precedent

Every major Australian financial institution and comparison site provides mortgage calculators:

- **ASIC MoneySmart**: "The results should not be taken as a substitute for professional advice."
- **Westpac**: "This information is general in nature and has been prepared without taking your personal objectives, circumstances and needs into account."
- **Aussie Home Loans**: Rate rise calculator showing impact of rate changes
- **money.com.au**: Rate change calculator with similar disclaimers
- **ANZ**: Home loan repayment calculator

### Risk Factors for the Mortgage Calculator

The calculator crosses into personal advice territory ONLY if it:

- Recommends a specific lender or product
- Suggests the user should fix or vary their rate
- Says things like "based on your situation, you should..."
- Takes into account the user's broader financial objectives or needs
- Uses language implying the user's personal circumstances have been considered

### Recommended Safeguards

- Label as **"Illustrative Calculator"** or **"Repayment Estimator"**
- Include disclaimer: "This calculator provides estimates for illustrative purposes only. It does not take into account your personal objectives, financial situation or needs."
- Do NOT pre-populate with "current" or "expected" rates that imply a prediction
- Allow users to enter their OWN details -- do not ask for personal financial goals

---

## 5. Safe vs Risky Language

### SAFE Language (Factual Information Tier)

| Context | Safe Phrasing |
|---------|--------------|
| Rate probability | "Market pricing implies a X% probability of a rate change" |
| Hawk score | "Current economic indicators lean hawkish/dovish" |
| Data presentation | "The latest CPI reading was X%, above/below the RBA target band" |
| Calculator | "Based on the figures you entered, estimated repayments would be..." |
| Trend description | "Market expectations have shifted toward..." |
| Score explanation | "The Hawk-O-Meter aggregates publicly available economic data" |
| Methodology | "The score is calculated using z-score normalisation of X indicators" |
| Attribution | "Source: ASX 30 Day Interbank Cash Rate Futures" |

### RISKY Language (Could Constitute Advice)

| Context | Risky Phrasing | Why It's Risky |
|---------|----------------|----------------|
| Rate prediction | "Rates **will** go up next month" | Statement of opinion/prediction |
| Product recommendation | "Now is a good time to **fix your rate**" | Recommendation about financial product |
| Action suggestion | "You should **refinance** before rates rise" | Recommendation to take specific action |
| Personalised guidance | "Based on **your loan**, you should consider..." | Takes into account personal circumstances |
| Market timing | "**Lock in** your rate now" | Recommendation about timing of action |
| Value judgment | "This is a **dangerous** time for variable rate borrowers" | Opinion intended to influence behaviour |
| Implied certainty | "The RBA **will definitely** raise rates" | Removes the uncertainty inherent in market pricing |

### Recommended Framing Patterns

- **Instead of**: "Rates will rise" -> **Use**: "Market pricing implies higher rates"
- **Instead of**: "You should fix your rate" -> **Use**: "The calculator shows the impact of different rate scenarios"
- **Instead of**: "This is bad for borrowers" -> **Use**: "A rate increase would change repayments as shown"
- **Instead of**: "We predict a rate hike" -> **Use**: "Current market expectations lean toward a rate increase"

---

## 6. Disclaimer Requirements and Examples

### Legal Basis for Disclaimers

If the Hawk-O-Meter stays within the "factual information" tier (no recommendations, no opinions intended to influence financial decisions), then technically a disclaimer is not legally required. However, disclaimers are **strongly recommended** as a defensive measure because:

1. The boundary between information and advice is subjective and context-dependent
2. ASIC has broad enforcement powers and the finfluencer crackdown shows increasing scrutiny of online financial content
3. The High Court in *Westpac v ASIC* found that disclaimers alone cannot convert personal advice into general advice, BUT they do help establish the provider's intent
4. Disclaimers protect against Australian Consumer Law claims of misleading conduct by managing user expectations

### Recommended Disclaimer Text for Hawk-O-Meter

#### Primary Disclaimer (footer of every page):

> **General Information Only**
>
> The information on this website is for general information purposes only. It is not intended to be, and should not be taken as, financial product advice, a recommendation, or a statement of opinion intended to influence your financial decisions.
>
> The Hawk-O-Meter score, probability indicators, and calculator tools aggregate publicly available data and perform mathematical computations. They do not take into account your personal objectives, financial situation, or needs.
>
> Before making any financial decisions, you should consider seeking independent professional advice from a licensed financial adviser.
>
> The creators of this website do not hold an Australian Financial Services Licence and are not authorised to provide financial product advice.

#### Calculator-Specific Disclaimer:

> **Illustrative Purposes Only**
>
> This calculator provides estimates based on the figures you enter. Results are illustrative only and should not be relied upon as a substitute for professional financial advice. Actual repayment amounts will depend on your specific loan terms, lender fees, and other factors not captured by this tool.

#### Data Attribution Notice:

> **Data Sources**
>
> Economic data is sourced from the Australian Bureau of Statistics, Reserve Bank of Australia, and ASX. Market-implied probabilities are derived from ASX 30 Day Interbank Cash Rate Futures pricing. Source data is used under Creative Commons Attribution 4.0 International License (CC BY 4.0) where applicable. The RBA and ABS do not endorse this website or guarantee the accuracy of derived calculations.

---

## 7. Competitor Disclaimer Analysis

### ASX RBA Rate Tracker

> *"This information is indicative only. It is not investment advice and readers should seek their own professional advice in assessing the effect of the information in their circumstances."*

> *"ASX Limited and its related corporations accept no responsibility for errors or omissions, including negligence, or for any damage loss or claim arising from reliance on the information."*

**Classification**: Indicative information (not advice). Note: ASX holds an AFS licence but disclaims the rate tracker as information, not advice.

### ASIC MoneySmart (moneysmart.gov.au)

> *"The information on this website is for general information only. It should not be taken as constituting professional advice from the website owner -- the Australian Securities and Investments Commission (ASIC)."*

> *"ASIC is not liable for any loss caused, whether due to negligence or otherwise arising from the use of, or reliance on, the information provided."*

> *"We don't lend money, arrange loans or provide personal financial advice."*

**Note**: Even ASIC -- the regulator itself -- uses comprehensive disclaimers on its own calculator tools.

### RBA Rate Watch (rbaratewatch.com)

> *"For informational purposes only. This is not financial advice."*

> *"Based on financial market data. Not a forecast, recommendation, or financial advice."*

**Classification**: Independent website, no AFS licence, positions as informational. Uses minimal but clear disclaimers.

### Canstar

> *"General advice provided by Canstar does not constitute personal advice as it does not take into account your financial situation, needs and objectives."*

**Note**: Canstar holds an AFS licence (AFSL 437917) because they actively rate and compare financial products (which constitutes general advice). This is a different activity from displaying economic data.

### Westpac (Mortgage Calculator)

> *"This information is general in nature and has been prepared without taking your personal objectives, circumstances and needs into account."*

> *"We recommend that you consult your financial adviser before taking out a loan."*

### Common Elements Across All Competitors

1. Statement that information is "general" and/or "indicative only"
2. Statement that it does not take personal circumstances into account
3. Recommendation to seek professional/independent advice
4. Limitation of liability for errors or reliance on information
5. Clear statement of what the tool is NOT (not a recommendation, not a forecast, etc.)

---

## 8. Data Attribution Requirements

### RBA Data

The RBA publishes most data under **Creative Commons Attribution 4.0 International License (CC BY 4.0)**. Requirements:

- **Attribution format**: "Source: Reserve Bank of Australia [year]" or "Source: RBA [year]"
- Must NOT suggest RBA endorsement of the Hawk-O-Meter
- Cannot charge users for access to RBA data without disclosing the data is freely available from the RBA
- Cannot misrepresent data or use it for unlawful purposes

### ABS Data

The Australian Bureau of Statistics publishes data under **Creative Commons Attribution 2.5 Australia** licence. Requirements:

- Attribute as "Source: Australian Bureau of Statistics"
- Include the specific dataset name/catalogue number where practical
- Cannot imply ABS endorsement

### ASX Data

ASX data (including futures-implied probabilities) has more restrictive terms:

- Not covered by Creative Commons
- The ASX's Terms of Use and data licensing policies apply
- If using ASX data, review their specific data use policy
- Derived calculations (i.e., computing your own probability from publicly available settlement prices) may have different terms than redistributing raw ASX data

### Recommendation for Hawk-O-Meter

- Include a "Data Sources" page or section listing all data sources with proper attribution
- Use the RBA's required attribution format
- Cite ABS catalogue numbers for specific datasets
- For ASX-derived data, note that probabilities are calculated from publicly available futures settlement data and attribute the ASX as the source exchange
- Update data attribution whenever data sources change

---

## 9. Australian Consumer Law Implications

### Section 18: Misleading or Deceptive Conduct

Section 18 of the Australian Consumer Law prohibits conduct that is **misleading or deceptive, or is likely to mislead or deceive**, in trade or commerce.

### Does "Trade or Commerce" Apply?

The term "trade or commerce" is interpreted broadly and includes any activity involved in supplying goods or services, advertising, or promoting a business. **It applies even to non-profit or free services** -- the key question is whether the conduct occurs in a commercial or business-like context.

For the Hawk-O-Meter:
- A free, open-source, non-commercial project is LESS likely to be caught by "trade or commerce" requirements
- However, if the site generates revenue (ads, sponsorship, donations), or builds a personal brand, it could be considered within "trade or commerce"
- Courts have interpreted "trade or commerce" very broadly

### Specific Risks Under ACL

1. **Presenting data inaccurately**: If the Hawk-O-Meter displays incorrect data, or the normalisation methodology produces misleading results, this could be misleading conduct
2. **Overstating certainty**: Presenting market-implied probabilities as certainties could mislead users
3. **Omitting material qualifications**: Failing to disclose limitations of the methodology or data freshness could be misleading
4. **Implied expertise**: Presenting the dashboard in a way that implies professional expertise when none exists

### Key Protections Under ACL

- ASIC INFO 269 states: *"You don't need to be licensed to breach the misleading or deceptive provisions"*
- This means even non-licensees must avoid misleading conduct about financial matters
- Penalties under ACL can include injunctions and damages

### Mitigation Strategies

1. **Be transparent about methodology** -- explain how scores are calculated
2. **Be transparent about data freshness** -- show when data was last updated
3. **Be transparent about limitations** -- acknowledge what the tool cannot do
4. **Use qualified language** -- "implies", "suggests", "based on", not absolute terms
5. **Attribute sources** -- show where data comes from so users can verify

---

## 10. Consequences of Non-Compliance

### For a Free, Non-Commercial, Open-Source Project

The practical enforcement risk for the Hawk-O-Meter is **LOW but not zero**. Here is a graduated assessment:

#### Low Risk Scenario (current design)

If the Hawk-O-Meter:
- Presents factual data with transparent methodology
- Uses "Market Expectation" framing (not "prediction")
- Includes proper disclaimers
- Does not recommend products or actions
- Is clearly a personal/open-source project

Then ASIC enforcement is very unlikely because:
- ASIC focuses enforcement on **commercial operators** causing consumer harm
- ASIC's 2025-2026 enforcement priorities target finfluencers who recommend specific financial products, not data aggregation tools
- The ASX operates a nearly identical tool without classifying it as advice
- There is no financial incentive creating a conflict of interest

#### Medium Risk Scenario

If the Hawk-O-Meter:
- Starts including language like "you should fix your rate" or "lock in now"
- Gains significant traffic and media attention
- Is perceived as influencing consumer financial decisions
- Contains errors that cause measurable consumer harm

ASIC could:
- Issue an informal warning or cease-and-desist letter
- Require changes to language or disclaimers
- Refer the matter for formal investigation

#### High Risk Scenario

If the project:
- Provides personalised recommendations based on user input
- Gains commercial sponsorship from financial product providers
- Becomes associated with selling or promoting specific financial products
- Deliberately misleads users about data or methodology

Potential consequences include:
- **Civil penalties** for providing unlicensed financial product advice (up to $1.11 million for individuals under s1311 Corporations Act)
- **Infringement notices** for misleading conduct
- **Court injunctions** requiring the site to be taken down or modified
- **ASIC warning notices** (as issued to 18 finfluencers in June 2025)

### ASIC Finfluencer Enforcement Context (2025)

In June 2025, ASIC issued warning notices to 18 social media finfluencers for providing unlicensed financial advice. The key characteristics of those cases were:

- Influencers were **recommending specific financial products** (CFDs, derivatives, specific stocks)
- They were often **compensated** by product issuers
- They **positioned themselves as trading experts**
- They **targeted retail consumers** with high-risk product recommendations

The Hawk-O-Meter does NONE of these things, which significantly reduces enforcement risk.

### Practical Bottom Line

For a free, non-commercial, open-source data dashboard with proper disclaimers that does not recommend financial products, ASIC enforcement action is **extremely unlikely**. The disclaimers serve primarily as:

1. A defensive legal shield if questions are ever raised
2. A signal to users to manage their expectations
3. Best practice alignment with industry norms
4. Protection against ACL misleading conduct claims

---

## 11. Compliance Checklist for Hawk-O-Meter

### MUST DO (Critical)

- [ ] **Include "General Information Only" disclaimer on every page** -- visible in the site footer, not hidden behind a link
- [ ] **Use "Market Expectation" language, NEVER "Prediction" or "Forecast"** throughout all content
- [ ] **Never recommend specific financial products** (do not say "fix your rate", "refinance", "switch lender")
- [ ] **Never suggest specific financial actions** based on the hawk score or probability gauge
- [ ] **Attribute all data sources** with proper format (e.g., "Source: Reserve Bank of Australia 2026")
- [ ] **Display data freshness** -- show when data was last updated and note any lag
- [ ] **State that creators do not hold an AFS licence** and are not authorised to provide financial product advice
- [ ] **Include calculator-specific disclaimer** stating results are illustrative only and do not consider personal circumstances
- [ ] **Do not collect or use personal financial information** beyond what users voluntarily enter into the calculator
- [ ] **Use qualified language everywhere** -- "implies", "suggests", "based on market pricing", not absolutes

### SHOULD DO (Strongly Recommended)

- [ ] **Create a dedicated "About / Disclaimer" page** with full legal text covering:
  - General information disclaimer
  - No-liability statement
  - Data source attribution
  - Methodology explanation
  - Limitation of liability
  - Recommendation to seek professional advice
- [ ] **Explain methodology transparently** -- users should understand the score is a mathematical derivation from public data, not editorial opinion
- [ ] **Use neutral colour framing** for the hawk gauge -- "Hawkish" (warm colours) vs "Dovish" (cool colours), NOT "Danger" vs "Safe"
- [ ] **Frame the calculator as a mathematical tool** -- "Repayment Estimator" or "Illustrative Calculator", not "Financial Planning Tool"
- [ ] **Include a brief disclaimer near the hawk score gauge itself** -- e.g., "Based on publicly available economic data. Not a forecast or recommendation."
- [ ] **Add a "How This Works" section** explaining the z-score normalisation and data aggregation process
- [ ] **Review all copy for inadvertent recommendations** before launch -- especially blog posts, tooltips, FAQ answers

### NICE TO HAVE (Additional Protection)

- [ ] **Link to ASIC MoneySmart** for users seeking actual financial advice
- [ ] **Include a "What This Tool Is Not" section** explicitly listing what the Hawk-O-Meter does not do
- [ ] **Add a cookie consent banner** for privacy compliance (Privacy Act 1988 / APPs)
- [ ] **Terms of Use page** covering intellectual property, limitation of liability, and acceptable use
- [ ] **Privacy Policy** if any user data is collected (even analytics cookies)
- [ ] **Periodic review** of language and disclaimers as the site evolves

### MUST NOT DO (Red Lines)

- [ ] **NEVER use language implying certainty** about future rate decisions ("rates WILL rise")
- [ ] **NEVER recommend or compare specific financial products** (lenders, loan types)
- [ ] **NEVER ask users for their financial objectives, goals, or personal financial situation** beyond calculator inputs
- [ ] **NEVER accept sponsorship or advertising from financial product providers** without reconsidering licensing obligations
- [ ] **NEVER claim expertise or professional qualifications** in financial advice
- [ ] **NEVER present the hawk score as a personal recommendation** ("based on your profile, you should...")
- [ ] **NEVER charge for access** to the tool without reviewing whether this changes the regulatory classification

---

## Sources and References

### Primary Regulatory Sources

- [ASIC RG 244: Giving information, general advice and scaled advice](https://www.asic.gov.au/regulatory-resources/find-a-document/regulatory-guides/rg-244-giving-information-general-advice-and-scaled-advice/)
- [ASIC RG 244 (PDF)](https://download.asic.gov.au/media/tkqi11il/rg244-published-13-december-2012-20211208.pdf)
- [Corporations Act 2001 s766B -- Meaning of financial product advice](https://www.austlii.edu.au/au/legis/cth/consol_act/ca2001172/s766b.html)
- [ASIC: Giving financial product advice](https://www.asic.gov.au/regulatory-resources/financial-services/giving-financial-product-advice/)
- [ASIC: Discussing financial products and services online](https://www.asic.gov.au/regulatory-resources/financial-services/giving-financial-product-advice/discussing-financial-products-and-services-online/)
- [ASIC Corporations (General Advice Warning) Instrument 2015/540](https://www.legislation.gov.au/F2015L01307/latest/text)
- [Australian Consumer Law -- Schedule 2, Competition and Consumer Act 2010](https://classic.austlii.edu.au/au/legis/cth/consol_act/caca2010265/sch2.html)

### Case Law

- [*Westpac Securities Administration Ltd v ASIC* [2021] HCA 3 (High Court)](https://www.brightlaw.com.au/case-note-high-court-defines-personal-advice/)
- [Gadens: When is financial product advice 'personal' and not 'general'?](https://www.gadens.com/legal-insights/when-is-financial-product-advice-personal-and-not-general-under-the-corporations-act-2001-cth/)
- [Herbert Smith Freehills: The landscape on general and personal advice](https://www.hsfkramer.com/notes/fsraustralia/2020-07/spotlight-on-general-and-personal-advice)

### Legal Analysis

- [Dwyer Harris: Walking the general advice tightrope](https://www.dwyerharris.com/blog/walking-the-general-advice-tightrope)
- [MinterEllison: ASIC v Westpac Securities Administration Limited](https://www.minterellison.com/articles/case-note-asic-v-westpac-securities-administration-limited-2019-fcafc-187)
- [Sprintlaw: Understanding Section 18 of Australian Consumer Law](https://sprintlaw.com.au/articles/understanding-section-18-of-australian-consumer-law-compliance-guide/)

### Competitor Disclaimers

- [ASX RBA Rate Tracker](https://www.asx.com.au/markets/trade-our-derivatives-market/futures-market/rba-rate-tracker)
- [ASIC MoneySmart Disclaimer](https://moneysmart.gov.au/about-us/disclaimer)
- [RBA Rate Watch](https://rbaratewatch.com/)
- [Canstar FSCG](https://www.canstar.com.au/canstar-fscg/)
- [Westpac Mortgage Calculator](https://www.westpac.com.au/personal-banking/home-loans/calculator/mortgage-calculator/)
- [RBA Copyright and Disclaimer Notice](https://www.rba.gov.au/copyright/)

### ASIC Enforcement

- [ASIC Enforcement Priorities](https://www.asic.gov.au/about-asic/asic-investigations-and-enforcement/asic-enforcement-priorities/)
- [ASIC: Finfluencer crackdown (June 2025)](https://www.asic.gov.au/about-asic/news-centre/news-items/asic-cracks-down-on-unlawful-finfluencers-in-global-push-against-misconduct/)

---

*Note: This research document is for planning purposes only. It does not constitute legal advice. The project team should consider consulting a qualified Australian lawyer specialising in financial services regulation before launch for a definitive legal opinion on compliance obligations.*
