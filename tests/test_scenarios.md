# Test Scenarios for Hybrid NL-to-SQL Engine

This document lists natural language queries tested on different database schemas to verify schema-agnostic functionality.

---

## Schema Variation 1
Database: `schema_variation_1.sql`  
Tables: `employees`, `departments`

| ID | Natural Language Query | Expected SQL | Expected Output Example |
|----|------------------------|---------------|--------------------------|
| 1 | How many employees are there? | `SELECT COUNT(*) FROM employees;` | 25 |
| 2 | Show all department names. | `SELECT dept_name FROM departments;` | HR, Finance, Sales |
| 3 | What is the average salary by department? | `SELECT dept_id, AVG(annual_salary) FROM employees GROUP BY dept_id;` | HR - 65k, Sales - 70k |

---

## Schema Variation 2
Database: `schema_variation_2.sql`  
Tables: `staff`, `offices`

| ID | Natural Language Query | Expected SQL | Expected Output Example |
|----|------------------------|---------------|--------------------------|
| 1 | How many employees are there? | `SELECT COUNT(*) FROM staff;` | 42 |
| 2 | List all office locations. | `SELECT office_location FROM offices;` | Chennai, Pune, Mumbai |
| 3 | Average salary by office. | `SELECT office_id, AVG(salary) FROM staff GROUP BY office_id;` | Chennai - 62k |

---

## Hybrid Query (Doc + SQL)
| ID | Natural Language Query | Data Source | Expected Result |
|----|------------------------|--------------|----------------|
| 1 | What is the company policy on remote work? | PDF document | “Employees can work remotely up to 2 days per week.” |
| 2 | How many employees are mentioned in Q1 report? | Database + Document | 120 |


