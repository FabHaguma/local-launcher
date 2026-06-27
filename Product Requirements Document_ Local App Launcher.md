# **Product Requirements Document (PRD)**

**Product Name:** Local App Launcher

**Platform:** Windows Desktop

**Tech Stack:** Python

**Document Version:** 1.0

## **1\. Overview and Objective**

The **Local App Launcher** is a lightweight Windows desktop utility built in Python. Its primary goal is to eliminate the repetitive friction of manually starting locally hosted applications.

Currently, the user must manually open a terminal, navigate to the correct directory, execute a start command, wait for the app to start, and copy/paste the localhost URL into a browser. This application reduces that entire workflow to a single click, spawning an independent terminal for the app's logs while automatically copying the relevant URL to the user's clipboard.

## **2\. Target Audience**

* Software Developers working on multiple local web projects.  
* Homelabbers and self-hosting enthusiasts running local services (e.g., local AI models, media servers, personal dashboards).  
* Any Windows user who frequently interacts with CLI-initiated web applications.

## **3\. User Flow**

1. **Launch:** User opens the "Local App Launcher" application.  
2. **Select:** The user is presented with a clean GUI displaying a list of configured applications as clickable links or buttons.  
3. **Execute:** The user clicks on a specific application.  
4. **Terminal Spawn:** The app automatically opens a new Windows terminal window (cmd.exe or powershell.exe), navigates to the required directory, and executes the start command.  
5. **URL Copy:** The application immediately copies the predefined localhost URL for that specific app to the Windows clipboard.  
6. **Notification:** A brief, non-intrusive UI message confirms "URL Copied to Clipboard."  
7. **Browse:** The user opens their web browser and pastes the URL to access their app.

## **4\. Core Features**

### **4.1. Dashboard / GUI**

* **App List:** A visual list of all configured local applications displaying the App Name and a description/URL.  
* **Launch Triggers:** Clickable buttons or hyperlinks for each application that trigger the launch sequence.

### **4.2. Terminal Execution Engine**

* **Independent Process Spawning:** The application must spawn a *new*, detached terminal window. The Python GUI must not freeze or wait for the terminal command to finish (as local servers run indefinitely).  
* **Working Directory Support:** The launcher must support changing the current working directory (cd) in the spawned terminal before running the start command (e.g., navigating to a specific React or Python project folder).

### **4.3. Clipboard Management**

* **Automated Copying:** Upon clicking an app launch trigger, the associated URL (e.g., http://127.0.0.1:8080) is silently and instantly copied to the system clipboard.

### **4.4. Configuration Management**

* **Persistent Storage:** App configurations must be stored locally (e.g., in a config.json file) so they persist between sessions.  
* **App Attributes:** Each registered application must store:  
  * id: Unique identifier  
  * name: Display name (e.g., "Stable Diffusion WebUI")  
  * path: Directory where the command should be run (e.g., C:\\AI\\stable-diffusion)  
  * command: The startup command (e.g., webui-user.bat or npm start)  
  * url: The localhost link to copy (e.g., http://127.0.0.1:7860)

## **5\. Optional / "Nice-to-Have" Features (v1.1+)**

* **App Editor UI:** A built-in graphical settings menu to Add, Edit, or Delete applications without manually editing the config.json file.  
* **Auto-Open Browser Toggle:** While the primary requirement is copying the link, a toggle could be added to simply launch the default Windows browser directly to that URL.  
* **Delay Timer for Browser:** If Auto-Open is implemented, allow a configurable delay (e.g., 5 seconds) to give the local server time to spin up before the browser hits the URL.

## **6\. Technical Specifications**

* **Language:** Python 3.10+  
* **OS Support:** Windows 10 / Windows 11  
* **GUI Framework:** CustomTkinter (recommended for a modern, dark-mode friendly look) or standard Tkinter (for zero external dependencies).  
* **Process Management:** Python's built-in subprocess module.  
  * *Implementation Note:* On Windows, spawning a new visible command prompt typically requires subprocess.Popen(\['cmd.exe', '/c', 'start', 'cmd.exe', '/k', f'cd /d {app\_path} && {app\_command}'\]).  
* **Clipboard Management:** \* Can use the Tkinter root .clipboard\_append() method or the external pyperclip library for robust cross-system clipboard handling.  
* **Data Storage:** Standard library json module reading/writing to apps.json in the same directory as the executable.

## **7\. Success Metrics**

* **Time Saved:** Reduction in time from wanting to open an app to having it running and pasted in the browser (should be \< 3 seconds of user interaction).  
* **Reliability:** The terminal reliably opens in the correct directory without crashing the main Python GUI.

## **8\. Development Milestones**

* **Phase 1: Proof of Concept (CLI/Backend)** \- Write Python scripts to successfully parse a JSON file, spawn a new CMD window executing a command, and copy a string to the clipboard.  
* **Phase 2: UI Implementation** \- Build the CustomTkinter interface and populate it dynamically from the JSON file. Wire the buttons to the Phase 1 backend functions.  
* **Phase 3: Refinement & Packaging** \- Add UI feedback (success messages), error handling (what if the path doesn't exist?), and compile the Python script into a standalone .exe using PyInstaller for easy everyday use.