# 📊 Hotel Booking Dashboard – Streamlit Visualization

This project is an **interactive dashboard** built with **Streamlit**, designed to visualize hotel booking data. It includes KPIs, time-based trends, guest profiles, market segmentation, booking behavior, and geolocation insights.

👉 **Live demo:**  
[https://data-viz-hotel.streamlit.app/](https://data-viz-hotel.streamlit.app/)


https://github.com/user-attachments/assets/d6213cec-2496-44c8-8115-f149805fbad8


> 💤 **App went to sleep?**  
If you see a message like _“This app has gone to sleep due to inactivity”_, just click the **“Yes, get this app back up!”** button and wait a few seconds. The app will reload automatically.
![image](https://github.com/user-attachments/assets/251bc686-50b8-4b55-a180-fc71576e6f2d)

---

## 📁 Directory Structure

```bash
Data-viz-hotel/
│
├── app.py                        # Main Streamlit dashboard
├── data/
│   ├── hotel_booking_cleaned.csv          # Cleaned hotel booking data
│   ├── occupancy_City_Hotel.csv           # Preprocessed daily occupancy data for City Hotel
│   ├── occupancy_Resort_Hotel.csv         # Preprocessed daily occupancy data for Resort Hotel
│   └── latitude_and_longitude_values.csv  # Country geolocation info
│   └── hotel_booking_original_data.csv    # The original hotel booking data
│
├── data cleaning/
│   └──  Clean data.ipynb         # Notebook for data cleaning
│
├── requirements.txt              # Python dependencies
└── README.md                     # Project documentation
```
---

## 📊 Datasets Used

The following open-source datasets are used in this project:

- **Hotel Booking Demand Dataset** (cleaned version):  
  [Kaggle: Hotel Booking Data](https://www.kaggle.com/datasets/mojtaba142/hotel-booking/data)

- **Geolocation Dataset** (for country coordinates):  
  [Kaggle: Geolocation Dataset](https://www.kaggle.com/datasets/liewyousheng/geolocation)

---

## 🚀 How to Run the App Locally

You can run this app locally using **Command Prompt (CMD)** on Windows or a **terminal in any IDE** (such as VS Code, PyCharm, etc.).

### ✅ First-Time Setup
1. **Clone the repository**

    ```bash
    git clone https://github.com/DeniseBi/Data-viz-hotel.git
    ```
    ```bash
    cd Data-viz-hotel
    ```

2. **(Optional) Create a virtual environment**

     On **Windows**:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

    On **macOS/Linux**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install the required packages**

   *Note: This step might take a few minutes depending on your internet connection and system.*
    ```bash
    pip install -r requirements.txt
    ```

---

### ▶️ Running the App

Before running the app, **make sure you are in Data-viz-hotel folder and your virtual environment is activated**  
 On **Windows**:
  ```bash
    venv\Scripts\activate
  ```

  On **macOS/Linux**:
  ```bash
    source venv/bin/activate
  ```
Then launch the dashboard using:

   ```bash
    streamlit run app.py
   ```

The dashboard will open in your browser at for example:  
http://localhost:8501
