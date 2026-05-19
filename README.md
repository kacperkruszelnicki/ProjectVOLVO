# 🚀 Project VOLVO

### Analysis and implementation of multi-source chatbot (majority in Confluence) when there are thousands of pages, no tagging, duplicated or obsolete articles

---

## Problem statement

A chatbot connected to Confluence (thousands of pages) and other sources (Stack overflow) produces low-quality, “nonsense” answers.
Confluence content is largely untagged, inconsistent, and contains duplicates/outdated pages.
Chatbot does not detect profiles and does not adjust the level of complexity of the answers to the profile (data engineers, business users, architects).

---

## Objectives

* Propose an end-to-end architecture for a knowledge chatbot that is grounded in sources and avoids hallucinations. Technology that works the best with non cloud Confluence and thousands of articles.
* Define a practical content preparation strategy that works – include main recommendation and minimal actions that could improve the quality of provided answers.
* Deliver actionable recommendations: “what to fix first” and expected impact.
* Provide an evaluation framework and test plan that can be executed on synthetic/redacted data.

---

## Assumptions and constraints

* No access to production Confluence pages for students.
* Available technologies are related to the Open AI and Copilot.

---

## Getting started

* Install uv
* After insstalling process, in the project folder enter the command - uv sync
* Create file .env and enter own access token from Hugging face
