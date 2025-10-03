# 🏥 SDC IEEE 11073 Project

This project demonstrates a **Service-oriented Device Connectivity (SDC)** setup compliant with the **IEEE 11073 standards**.

It includes:

* Multiple **SDC Providers** simulating medical devices.
* A single **SDC Consumer** that discovers and interacts with them.

---

## 📁 Project Structure

```
SDC_IEEE11073
├── env/                     # Python virtual environment for the project
├── sdc_consumer/            # The SDC Consumer application
│   ├── app/                 # Main application logic for the consumer
│   └── requirements.txt     # Python dependencies for the consumer
├── sdc_providers/           # Contains all SDC Provider applications
│   ├── provider01/          # A simulated medical device
│   │   ├── main.py          # Main execution script for provider 1
│   │   ├── mdib.xml         # Medical Device Information Base for provider 1
│   │   └── requirements.txt # Python dependencies for provider 1
│   └── provider2/           # A second simulated medical device
│       ├── main.py
│       ├── mdib.xml
│       └── requirements.txt
└── README.md                # This setup and usage guide
```

---

## 🚀 How to Run the Simulation

Running this project requires **three separate terminal windows**:

* One for each provider (`provider01` and `provider2`).
* One for the consumer.

⚠️ **Important**: Start the **providers** before running the **consumer**.

---

### 1️⃣ Environment Setup

In **each terminal**, navigate to the project root and activate the virtual environment:

```bash
# Navigate to the project root
cd path/to/SDC_IEEE11073

# Activate the virtual environment
source env/bin/activate
```

---

### 2️⃣ Install Dependencies

Install the required dependencies for each component:

```bash
# Install consumer dependencies
pip install -r sdc_consumer/requirements.txt

# Install dependencies for provider01
pip install -r sdc_providers/provider01/requirements.txt

# Install dependencies for provider2 (if different)
pip install -r sdc_providers/provider2/requirements.txt
```

---

### 3️⃣ Run the SDC Providers

Open **two separate terminals**, one for each provider.

➡️ **Terminal 1 – Run provider01**

```bash
cd sdc_providers/provider01
python main.py
```

You should see output indicating that **Provider 1** is running and waiting for a connection.

➡️ **Terminal 2 – Run provider2**

```bash
cd sdc_providers/provider2
python main.py
```

You should see output indicating that **Provider 2** is running.

---

### 4️⃣ Run the SDC Consumer

With both providers running, open a **third terminal** for the consumer:

```bash
cd sdc_consumer

# Run the consumer application (assuming entry point is in 'app')
python -m app
```

✅ The consumer will start, discover the providers, and connect to both.
You will see log outputs in **all three terminals** as the applications interact.

---

Would you like me to also add a **diagram** (ASCII or image-ready) showing how the consumer and providers interact in this setup? That would make the README even clearer.
