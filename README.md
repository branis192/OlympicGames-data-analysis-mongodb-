# Olympic & World Athletics Data Analysis (MongoDB)

## 📌 Project Overview
This project focuses on analyzing a large-scale dataset of Olympic and World Athletics results using **MongoDB**. The dataset contains over **150,000 athlete records** and comprehensive results spanning several decades. The goal was to build a robust NoSQL environment to perform complex statistical queries, handle data cleaning, and execute advanced aggregation pipelines.

## 🛠️ Tech Stack
* **Database:** MongoDB Server 8.0.15 (Linux x86_64)
* **Client:** MongoDB Shell (mongosh)
* **Tools:** Bash scripting (sed for data cleaning), Git

## 📂 Dataset Structure
The project utilizes four primary collections imported via `mongoimport`:
* `athletes`: Personal details and metadata of participants.
* `results`: Detailed records of every competition entry (Event, Year, Medal, NOC).
* `events`: Metadata regarding Olympic disciplines and their active years.
* `editions`: Chronological data of various games.

## 🚀 Key Features & Queries
The project implements a series of high-level MongoDB queries to extract meaningful insights:
1. **Historical Trends:** Calculating the number of disciplines per edition.
2. **Gender Analysis:** Tracking female athlete participation growth before and after the year 2000.
3. **Performance Metrics:** Identifying the most decorated athletes globally and per discipline, including tie-breaking (ex-aequo) logic.
4. **Global Distribution:** Aggregating athlete counts by sex and country (NOC).
5. **Rare Disciplines:** Identifying sports appearing in fewer than 10 editions.

## 🔧 Data Cleaning & Installation
During the ingestion phase, data integrity was ensured by:
* Converting invalid JSON tokens (e.g., `NaN` values from Python exports) to valid `null` values using `sed`.
* Utilizing `--jsonArray` and `--drop` flags during `mongoimport` to ensure clean, repeatable database builds.

## 📈 Example Query (Top Athletes)
```javascript
db.results.aggregate([
  { $match: { medal: { $ne: "na" } } },
  { $group: { _id: "$athlete_name", total: { $sum: 1 } } },
  { $sort: { total: -1 } },
  { $limit: 10 }
]);