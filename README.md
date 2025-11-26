# LevKatan – Baby Item Lending Platform

## 📖 Project Overview
LevKatan is a web application designed to manage a lending center for baby and child items (strollers, cribs, car seats, playpens, etc.).  
The system allows families to borrow useful items for their children free of charge, while administrators can efficiently manage inventory, requests, and returns.

---

## 🎯 Goals and Objectives (SMART)

### Goal 1: Streamline administrator processes
- **Objective 1.1:** Reduce average processing time for a new loan request to **≤ 5 minutes** within 3 months of launch.
- **Objective 1.2:** Ensure **98% inventory accuracy** (system data vs. physical stock) by end of semester, using barcode scanning or real-time status updates.

### Goal 2: Improve user experience for families
- **Objective 2.1:** Allow **100% of registered users** to view catalog and item availability online, 24/7, from the MVP release.
- **Objective 2.2:** Send **automatic return reminders** (email/SMS) to 100% of borrowers 3 days before due date, reducing late returns by 30% in the first quarter.

---

## 👥 Target Audience

- **Administrators (Primary users):**  
  Need a simple interface to add/edit items, manage stock statuses (available, borrowed, under repair), approve/refuse requests, track returns, and view basic reports.

- **Families (End users):**  
  Need to register and be verified, browse a clear catalog (with categories, search, and filters), submit loan requests, and view their borrowing history and return dates.

---

## 📦 Core Features

### Essential
- User registration and login (families and administrators).
- Inventory management (add, edit, delete items and categories).
- Public catalog with search and filtering.
- Loan request process.
- Admin interface for approving/refusing requests.
- Return tracking and status updates.

### Additional (Nice-to-have)
- Ratings and reviews for items.
- Automatic return reminders (email/SMS).
- Admin dashboard with charts and statistics.
- Waiting list for highly demanded items.

---

## 🛠️ Technology & Methodology
- **Backend:** (to be defined, e.g., .NET Core, Node.js, or Python Flask)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** PostgreSQL (managed via pgAdmin)
- **Project Management:** Agile methodology with Azure DevOps
- **Cloud/Hosting:** Azure 

---

## 📅 Constraints
- **Duration:** Limited to one semester, with a fixed deadline.
- **Team:** 3 students (Database, Frontend, Backend).
- **Security:** User data (name, phone number, email) must be stored securely and confidentiality guaranteed.

---

## 📂 Database Design (Initial)
- **Table: `user`**
  - `id`, `first_name`, `last_name`, `email`, `username`, `phone_number`, `password`, `role`
- **Table: `product`**
  - `id`, `product_name`, `category`, `publish_date`, `status`, `owner_id`

---

## 🚀 Next Steps
1. Set up PostgreSQL database (`LevKatan`) with initial tables.
2. Implement backend API to connect database with frontend.
3. Build frontend interface for catalog browsing and loan requests.
4. Configure Azure DevOps boards and dashboards for sprint tracking.

---

## 📌 Project Vision
LevKatan aims to provide families with easy access to essential baby items while reducing the workload for administrators. By centralizing inventory and requests in a modern web application, the project supports community sharing and sustainability.
