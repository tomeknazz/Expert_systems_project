# Temperature Anomaly Detection

## Project Goal
This project aims to detect unusual temperature behavior in weather measurements. It implements a robust data processing pipeline that ingests data from a Weather REST API, processes it to find statistical outliers, and generates actionable analytical outputs.

---

## Architecture & Data Pipeline
The project follows a decoupled architecture, separating data engineering stages into distinct layers to fulfill best practices:

* **Raw Storage:** Persists incoming JSON records directly from the Weather API for traceability and future reprocessing.
* **Processing Layer:** Normalizes timestamps and applies rolling statistical calculations.
* **Curated Layer:** Isolates flagged anomalies into a dedicated, clean dataset.
* **Analytical Output:** Generates visualizations and structured tables for monitoring dashboards.

---

## Analytical Methodology
A robust statistical approach utilizing **Rolling Mean & Z-Score Analysis** was chosen to account for natural daily temperature fluctuations.

* **Timestamp Normalization:** Data retrieved from the REST API is sorted chronologically.
* **Rolling Windows:** We calculate a moving average (`rolling_mean`) and rolling standard deviation (`rolling_std`) over a 24-period window. This contextualizes the current temperature against recent trends, rather than a fixed historical average.
* **Z-Score Calculation:** For every data point, a Z-score is calculated using the formula $Z=(X-\mu)/\sigma$, where $X$ is the current temperature, $\mu$ is the rolling mean, and $\sigma$ is the rolling standard deviation.
* **Rule-based Detection:** Measurements with an absolute Z-score greater than 2.0 are flagged as anomalies. This threshold isolates highly irregular temperatures that deviate significantly from expected local patterns.

---

## Assumptions & Limitations

### Assumptions
* The API delivers consistent hourly or regular measurement intervals.
* The 24-period rolling window is specifically optimized for 24-hour daily cycles.

### Limitations
* Initial periods (before the window is fully populated) use smaller sample sizes for moving averages, which might lead to higher sensitivity early in the dataset.
* Extreme weather events (like sudden storms) might be flagged as anomalies. While statistically correct, this does not necessarily indicate a sensor or measurement error.

### Possible Improvements
* Implementing complex algorithms like ARIMA or Isolation Forests.
* Upgrading to multivariate anomaly detection by including pressure and humidity alongside temperature.

---

## Conclusions

* **Pipeline Efficiency:** The decoupled architecture successfully separates raw data ingestion, processing, and analytical outputs. Saving raw data ensures traceability and allows for reprocessing without unnecessarily querying the API again.
* **Detection Efficacy:** The dynamic Z-score method effectively isolates true anomalies (sudden spikes or drops) while ignoring natural diurnal temperature shifts. A static threshold model would likely trigger false positives under the same conditions.
* **Actionable Output:** The generated `anomaly_table.csv` and visual charts provide clear, easily interpretable results ready to be used by downstream monitoring teams.