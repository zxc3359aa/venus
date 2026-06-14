# Venus Product Intelligence Design

Date: 2026-06-14

## Purpose

This slice adds a deeper product-intelligence contract for Venus. It turns a product dossier into structured analysis for brand backing, filing status, ingredient risk, supplier documents, test reports, historical controversy, claim risk, and precise retrieval tasks.

It supports the user's requirement that Venus can automatically analyze product filings, ingredient details, ingredient suppliers, testing evidence, brand backing, and historical controversy before using a product in content, commercial scripts, or reply guidance.

## Data Source

The first input shape is `data/samples/product_intelligence.json`.

It may contain:

- Product identity: brand, name, filing ID, manufacturer, and category.
- Brand backing: dermatologist quotes, lab collaborations, media references, certificates, or campaign materials.
- Ingredient records: role, risk, supplier, COA, and test report references.
- Supplier documents and COA status.
- Test report status and test scope.
- Historical controversies from comments, creators, complaints, or imported research.
- Claim text and evidence IDs.
- Live connector intent.

The source is labeled as manual or imported product dossier data. Live NMPA, supplier, brand, social search, or crawler access remains disabled in this slice.

## Output

`build_product_intelligence_report(payload)` returns:

- `workflow: product_intel`.
- Venus namespace and dry-run status.
- Source metadata and freshness notes.
- Summary metrics for backing, ingredients, supplier documents, test reports, controversies, forbidden claims, retrieval tasks, and approval-gated actions.
- `product_identity` and `filing_check`.
- `brand_backing` with verification states.
- `ingredient_matrix` with roles, risks, suppliers, COA, test reports, and content notes.
- `supplier_document_checks` and `test_report_checks`.
- `controversy_scan`.
- `claim_risk` with forbidden claims and safe wording boundary.
- `retrieval_plan` with precise next tasks.
- `approval_records` for live connector enablement and claim review.
- `external_actions: []`.

The CLI supports:

```bash
venus product-intel data/samples/product_intelligence.json
```

The Feishu dry-run adapter supports:

```text
/venus product-intel
```

Agent Run also summarizes product intelligence when the payload includes `product_intelligence`.

## Approval Boundaries

- Local product dossier structuring is level 1 internal analysis.
- Live product filing, supplier-document, test-report, or controversy retrieval is level 2 and requires manual approval.
- Claim-sensitive product wording requires level 2 review.
- No filing query, supplier request, brand contact, crawler, social search, customer message, or publishing action is executed.

## Safety

- Config must use a Venus namespace and reject Xiaolongxia references.
- Dry-run mode is required.
- Secret-like fields are redacted from outputs.
- Outputs keep `external_actions: []`.
- Future live retrieval must add source attribution, credential checks, privacy review, rate limits, audit logs, and rollback controls.

## Testing

Acceptance requires:

- Unit tests for brand backing, filing, ingredient matrix, supplier documents, test reports, controversy scan, claim risk, retrieval plan, approval records, redaction, and isolation.
- CLI smoke test for `venus product-intel`.
- Feishu dry-run test for `/venus product-intel`.
- Agent Run test proving product-intel summaries are included in the operating cycle.
- Full `pytest -v` pass.
