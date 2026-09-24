# Blueprint Sources

Reference repositories were retrieved on 2026-09-24 as shallow clones in ignored subdirectories alongside this public index. The recorded commits are fixed Phase 0 reference points. No upstream dependencies or scripts were installed or executed.

## CoFolio

- Public URL: https://github.com/yogur/cofolio
- Local checkout state: `main`, shallow clone
- Commit: `ffb3203075267a7b4093c4d2aa49449d9357d188`
- License file: `LICENSE`
- Preliminary license: MIT
- Relevance: primary candidate for portfolio context, maintenance, and contribution workflows.
- Preliminary constraint: preserve the MIT copyright and permission notice if substantial code is reused. Actual reuse suitability remains subject to the Phase 1 code audit.

## FinRobot

- Public URL: https://github.com/AI4Finance-Foundation/FinRobot
- Local checkout state: `master`, shallow clone
- Commit: `6d6ccd32c1b8b1904dc656cf06897438aba3daec`
- License files: `LICENSE`, `NOTICE`
- Preliminary license: Apache License 2.0
- Relevance: candidate for specialist organization, research provenance, criticism, and synthesis patterns.
- Preliminary constraint: redistribution obligations include the license and applicable notices. The recorded notice also contains trademark terms. Detailed applicability remains subject to Phase 1 review.

## AI Finance Assistant

- Public URL: https://github.com/iOSNinja/ai-finance-assistant
- Local checkout state: `main`, shallow clone
- Commit: `c835596ba86c5d1f85f079776a113184073f9e71`
- License file: `LICENSE`
- Preliminary license: source-available for viewing only; no general permission to redistribute or reuse
- Relevance: architecture-only reference for orchestration and computation/reasoning separation.
- Preliminary constraint: do not copy source code. Any reuse would require explicit written permission from the copyright holder.

## Wealthfolio

- Public URL: https://github.com/wealthfolio/wealthfolio
- Local checkout state: `main`, shallow clone
- Commit: `857e69a96f39d5b96db6bc5c8ce6c9086fb7b03c`
- License files: root `LICENSE`; `packages/addon-sdk/LICENSE`
- Preliminary licenses: GNU Affero General Public License v3.0 for the main repository; MIT for the addon SDK subpackage
- Relevance: candidate reference for instruments, accounts, holdings, transactions, allocation, and currency models.
- Preliminary constraint: main-project code reuse may trigger AGPL obligations and must not occur before a component-level license review. The addon SDK has separate MIT terms.

## Ghostfolio

- Public URL: https://github.com/ghostfolio/ghostfolio
- Local checkout state: `main`, shallow clone
- Commit: `af3d72f94c61d0d0380798f21567de70e4d4adc6`
- License file: `LICENSE`
- Preliminary license: GNU Affero General Public License v3.0
- Relevance: candidate reference for buy-and-hold workflows, portfolio models, performance, and risk concepts.
- Preliminary constraint: code reuse may trigger AGPL obligations and must not occur before detailed license and architecture review.

## PyPortfolioOpt

- Public URL: https://github.com/PyPortfolio/PyPortfolioOpt
- Local checkout state: `main`, shallow clone
- Commit: `a6638d2e06dae6f444fd022cfd4b3c528902a85b`
- License file: `LICENSE`
- Preliminary license: MIT
- Relevance: candidate deterministic quantitative library if later requirements justify its assumptions and dependency cost.
- Preliminary constraint: preserve the MIT copyright and permission notice for reused material. Dependency necessity remains unresolved.

## Phase 0 limitations

These are preliminary identifications from license files at the recorded commits, not legal advice or a component-level reuse determination. Phase 1 must inspect relevant source paths, bundled assets, dependency metadata, notices, and any component-specific terms before recommending reuse. Public availability alone is not permission to copy code.
