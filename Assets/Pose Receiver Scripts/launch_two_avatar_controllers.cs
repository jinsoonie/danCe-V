using UnityEngine;
using System.Diagnostics;
using System.IO;
using System.Collections;
using UnityEngine.SceneManagement;
using System.Net;
using System.Net.Sockets;
using System.Text;



public class DanceAvatarController : MonoBehaviour
{
    // public pauseMenu UI
    public GameObject pauseMenu;  // assigned pause menu UI in the Inspector
    // private keep track of isPaused state
    private bool isPaused = false;
    

    void Start()
    {
        UnityEngine.Debug.Log("Unity called Python with Type 1 (Live Cam Feed).");
        // Start the live webcam feed process (Type 1)
        StartCoroutine(RunPythonProcess(true, "", false));

        // // Start the reference JSON process (Type 3)
        // // Update the path if JSON file is stored elsewhere.
        // string referenceJsonPath = Application.dataPath + "/Pose Receiver Scripts/reference_output.json";
        // UnityEngine.Debug.Log("Unity called Python with Type 3 (Ref json sent).");
        // StartCoroutine(RunPythonProcess(false, referenceJsonPath, true));
    }

    void Update()
    {
        // Start the reference JSON process (Type 3) when space is pressed
        if (Input.GetKeyDown(KeyCode.Space))
        {
            // Update the path if JSON file is stored elsewhere.
            string referenceJsonPath = Application.dataPath + "/Pose Receiver Scripts/reference_output.json";
            UnityEngine.Debug.Log("Unity called Python with Type 3 (Ref json sent).");
            StartCoroutine(RunPythonProcess(false, referenceJsonPath, true));

            // Send START signal to Python (to begin comparison)
            SendComparisonStartSignalToPython();
        }

        // Toggle pause state with the escape key
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            if (isPaused)
                ResumeGame();
            else
                PauseGame();
        }
    }

    void PauseGame()
    {
        isPaused = true;
        Time.timeScale = 0f;  // Freeze game time
        pauseMenu.SetActive(true);  // Display the pause menu
    }

    void ResumeGame()
    {
        isPaused = false;
        Time.timeScale = 1f;  // Resume game time
        pauseMenu.SetActive(false);  // Hide the pause menu
    }

    // Called when the Restart button is clicked
    public void RestartLevel()
    {
        // Resume time in case the game is paused.
        Time.timeScale = 1f;
        // Reload the current scene.
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }

    // Called when the Main Menu button is clicked
    public void LoadMainMenu()
    {
        // Resume time before loading the main menu.
        Time.timeScale = 1f;
        // Load the MainMenu scene (ensure that your scene name matches exactly).
        SceneManager.LoadScene("Main Menu");
    }

    IEnumerator RunPythonProcess(bool useLiveCamera, string filePath, bool sendPreformedJson)
    {
        string pythonPath = "python"; // Make sure python is installed and in your PATH
        string scriptPath = Application.dataPath + "/Pose Receiver Scripts/pose_sender.py";
        string arguments = "";

        // Configure the arguments based on the process type.
        if (useLiveCamera)
        {
            // Type 1: live webcam feed (useLiveCamera = true, (potentially) file path to ref, sendPreformedJson = false)
            arguments = $"\"{scriptPath}\" True \"\" False";
        }
        else if (sendPreformedJson)
        {
            // Type 3: sending pre-generated JSON (useLiveCamera = false, file path provided, sendPreformedJson = true)
            arguments = $"\"{scriptPath}\" False \"{filePath}\" True";
        }

        ProcessStartInfo processInfo = new ProcessStartInfo
        {
            FileName = pythonPath,
            Arguments = arguments,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true
        };

        Process process = new Process { StartInfo = processInfo };

        // Attach asynchronous event handlers to capture output and errors.
        process.OutputDataReceived += (sender, args) =>
        {
            if (!string.IsNullOrEmpty(args.Data))
                UnityEngine.Debug.Log($"Python Output: {args.Data}");
        };

        process.ErrorDataReceived += (sender, args) =>
        {
            if (!string.IsNullOrEmpty(args.Data))
                UnityEngine.Debug.Log($"Python Error: {args.Data}");
        };

        process.Start();
        process.BeginOutputReadLine();
        process.BeginErrorReadLine();

        // // Wait until the Python process exits
        // while (!process.HasExited)
        // {
        //     yield return null;
        // }

        // or just end Unity coroutine for now
        yield break;
    }

    // tell pose_sender to start displaying comparison metrics only when this is sent (ref avatar is triggered as well)
    void SendComparisonStartSignalToPython()
    {
        using (UdpClient udpClient = new UdpClient())
        {
            try
            {
                string message = "START_COMPARISON";
                byte[] data = Encoding.ASCII.GetBytes(message);
                udpClient.Send(data, data.Length, "127.0.0.1", 5010); // 5010 is where pose_sender.py is listening for START_SIGNAL
                UnityEngine.Debug.Log("Unity Sent START_COMPARISON signal to Python.");
            }
            catch (System.Exception ex)
            {
                UnityEngine.Debug.LogError($"Unity Error sending START_COMPARISON: {ex.Message}");
            }
        }
    }

}
