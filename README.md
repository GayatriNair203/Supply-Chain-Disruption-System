# Supply-Chain-Disruption-System
An AI-powered supply chain disruption intelligence system built with LangGraph and Streamlit. It analyzes shipment data, weather, traffic, and news, calculates operational risk, applies company policies, recommends actions, and routes high-risk cases for human review.


# 📦 Supply Chain Disruption Intelligence System

An AI-powered Supply Chain Disruption Intelligence System built with **LangGraph**, **LangChain**, and **Streamlit**. The application analyzes shipment information using multiple real-world data sources, evaluates operational risk, applies company policies, and generates logistics recommendations to support supply chain decision-making.

---

# Features

* 📦 Shipment lookup from a SQLite database
* 🌦️ Real-time weather analysis
* 🚚 Route and traffic analysis
* 📰 News intelligence for disruption detection
* ⚠️ Risk scoring (0–100)
* 📖 Company policy retrieval
* 🤖 AI-powered disruption analysis
* 🚛 Logistics decision recommendations
* 👤 Human-in-the-loop approval routing
* 📄 Executive PDF report generation
* 📧 Email report delivery
* 🌐 Interactive Streamlit dashboard

---

# Technologies Used

* Python
* LangGraph
* LangChain
* OpenAI
* Streamlit
* SQLite
* Weather API
* TomTom Routing API
* News API

---

# System Workflow

```text
                        START
                          │
                          ▼
                Enter Shipment ID
                          │
                          ▼
                 Retrieve Shipment
                   from Database
                          │
          Shipment Found?
          ┌───────────────┴───────────────┐
          │                               │
         No                              Yes
          │                               │
          ▼                               ▼
     Display Error              Gather Intelligence
                                         │
              ┌──────────────┬──────────────┬──────────────┐
              │              │              │
              ▼              ▼              ▼
      Weather Analysis   Route Analysis   News Analysis
              │              │              │
              └──────────────┴──────────────┘
                          │
                          ▼
                 Calculate Risk Score
                          │
                          ▼
              Retrieve Company Policies
                          │
                          ▼
          Disruption Detection Agent
                          │
                          ▼
          Logistics Decision Agent
                          │
                          ▼
          Human Approval Required?
               ┌─────────┴─────────┐
               │                   │
              No                  Yes
               │                   │
               ▼                   ▼
      Auto Approve          Human Review
               │                   │
               └─────────┬─────────┘
                         ▼
              Generate Executive Report
                         │
                         ▼
                 Send Email Report
                         │
                         ▼
                        END
```

---

# Project Structure

```text
SupplyChainDisruptionSystem/
│
├── app.py
├── init_db.py
├── check_db.py
│
├── workflow/
│   ├── graph.py
│   ├── nodes.py
│   └── state.py
│
├── services/
│   ├── disruption_agent.py
│   ├── logistics_decision_agent.py
│   ├── weather_tool.py
│   ├── news_tool.py
│   ├── news_intelligence.py
│   ├── route_tool.py
│   ├── decision_engine.py
│   ├── disruption_engine.py
│   └── policy_retriever.py
│
├── models/
│   └── shipment_db.py
│
├── rules/
│   └── rules_engine.py
│
├── knowledge_base/
│   └── company_policies.txt
│
└── reports/
```

---

# Risk Assessment

The system evaluates shipment risk by combining information from multiple sources:

* Shipment priority
* Shipment status
* Weather conditions
* Route delays
* Traffic congestion
* News disruptions
* Business rules
* Company policies

Each factor contributes to an overall operational risk score ranging from **0–100**.

---

# AI Decision Pipeline

The application uses two AI agents:

### 1. Disruption Detection Agent

* Summarizes shipment risks
* Identifies disruption causes
* Explains operational impact

### 2. Logistics Decision Agent

* Reviews disruption analysis
* Applies company policies
* Generates logistics recommendations
* Determines whether human approval is required

---

# Human-in-the-Loop

High-risk shipments are automatically routed for manual review before approval.

The reviewer can:

* Approve shipment
* Reject recommendation
* Review AI analysis
* Review company policy references

---

# Getting Started

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Initialize Database

```bash
python init_db.py
```

## Run Application

```bash
streamlit run app.py
```

---

# Future Improvements (Version 2)

* Evaluation framework for measuring AI performance
* LangGraph checkpointing and workflow persistence
* Parallel tool execution
* Decision comparison and scoring
* Scenario simulation
* Policy Retrieval-Augmented Generation (RAG)
* Comprehensive testing and evaluation
* Enhanced dashboard analytics

---

# License

This project is intended for educational and portfolio purposes.
