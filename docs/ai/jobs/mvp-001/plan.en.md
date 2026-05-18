# Plan: MVP-001 - Project Initialization and Core Architecture Skeleton

## Goal
Initialize the US stock automated paper-trading system by building the foundational architectural skeleton (Strategy -> Risk Engine -> OMS) and strictly enforcing safety rules.

## Context
This is the first implementation step (MVP-001). We need a solid, type-safe foundation that ensures all orders pass through the mandatory pipeline and that paper trading is the default mode.

## In scope
- **Project Bootstrapping**: Initialize a TypeScript/Node.js project structure (if not already present) or define the sub-directory for the trading engine.
- **Type Definitions**: Define core interfaces and types:
    - `OrderIntent`: Non-executable intent created by Strategy.
    - `ExecutableOrder`: Finalized order created ONLY by the OMS.
    - `MarketData`, `Position`, `Trade`.
- **Pipeline Implementation (Skeletons)**:
    - `Strategy`: A base class or interface that produces `OrderIntent`.
    - `RiskEngine`: A component that validates `OrderIntent` (e.g., checks for market orders, which are disabled by default).
    - `OMS (Order Management System)`: The only component authorized to convert a validated `OrderIntent` into an `ExecutableOrder`.
- **Broker Adapter (Mock)**: A simple adapter for paper trading that logs order execution.
- **Configuration & Safety**:
    - Load settings from `.env`.
    - Ensure `PAPER_TRADING` is set to `true` by default.
    - Implement "Fail closed" logic for the Risk Engine.

## Out of scope
- Real broker API integration (Alpaca, IBKR, etc.).
- Live trading activation or validation logic.
- Complex trading strategies.
- Persistence (Database).
- Web Dashboard.

## Acceptance criteria
- [ ] Directory structure is established (e.g., `src/core`, `src/adapters`, `src/types`).
- [ ] `OMS` is the only place where an `ExecutableOrder` can be instantiated.
- [ ] `RiskEngine` contains a check that rejects market orders by default.
- [ ] A mock trading loop can be executed: `MarketData -> Strategy -> RiskEngine -> OMS -> MockBroker`.
- [ ] `PAPER_TRADING=true` is enforced unless explicitly overridden in `.env` (and even then, blocked by safety guards for this phase).
- [ ] Unit tests for the pipeline skeleton are included.

## Suggested approach
1. **Setup**: Initialize the project and install necessary dependencies (e.g., `typescript`, `dotenv`, `jest`).
2. **Types**: Create `src/types/index.ts` to define the immutable structure of orders and intents.
3. **Core**: Implement base classes for Strategy, Risk Engine, and OMS in `src/core/`.
4. **Adapter**: Implement `MockBrokerAdapter` in `src/adapters/`.
5. **Validation**: Add a simple script in `scripts/` or a test case in `tests/` to verify the end-to-end flow.

## Risks & open questions
- **Language**: Assuming TypeScript for type safety as it's critical for the "OMS exclusivity" rule.
- **Project Root**: Should the trading engine live in a dedicated `engine/` folder or in the root? (Assuming a dedicated folder for better organization).

## Files likely to change
- `package.json` (New)
- `tsconfig.json` (New)
- `.env.example` (New)
- `src/**/*.ts` (New)
- `tests/**/*.ts` (New)
