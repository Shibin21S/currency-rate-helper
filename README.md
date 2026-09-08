# Currency Rate Helper

## What This Project Does
A daily-updating helper tool that checks foreign currency exchange rates
across major Canadian banks and tells users which bank currently offers
the best deal for a given currency exchange.

## The Problem It Solves
People who want to exchange currency (e.g., CAD to USD) normally have to
check multiple bank websites manually to find the best rate. This project
automates that comparison and presents it in one place.

## Scope (Milestone 1 — Core Version)
- Check exchange rates from Canada's major banks daily
- Compare buy/sell rates against the Bank of Canada baseline rate
- Automatically identify which bank offers the best deal, per currency
- Publish results as a simple, human-readable web page (updated daily)

## Stretch Goals (Later Milestones)
- Google Form for users to request a personalized recommendation
- AI-generated response emailed back to the user
- Additional criteria (e.g., travel purpose, transaction amount)

## Tech Stack (Planned)
- **Claude Skill** — defines the logic for comparing bank rates
- **Claude Agent** — runs the skill to fetch and process daily rates
- **GitHub Actions** — scheduled daily trigger
- **GitHub Pages** — free hosting for the results page
- **Bank of Canada Valet API** — reliable fallback baseline rate data
- **Google Sheets / Forms + Make** — stretch-goal personalization pipeline

## Status
🚧 In progress — Milestone 1 (core comparison + daily webpage) underway.
