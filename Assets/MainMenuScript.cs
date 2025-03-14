using UnityEngine;
using UnityEngine.SceneManagement;
using SFB;  // StandaloneFileBrowser used to select .mp4 file
using System.Diagnostics;   // used to run Python script from this C# file (Process class)
using System.IO;
using UnityEngine.UI;
using System.Collections;
using TMPro; // because Unity now uses TextMeshPro

public class MainMenuScript : MonoBehaviour
{
    // function for once video uploaded+processing completed,
    public void PlayGame()
    {
        SceneManager.LoadSceneAsync("Dance Avatar Scene");
    }

    public TMP_Text statusText;  // Assign a UI Text-TextMeshPro element in Unity

    void Start()
    {
        statusText.text = "Select a .mp4 dance video to analyze.";
    }

    public void SelectVideo()
    {
        string folderPath = Application.dataPath; // Game's local folder (should be same path as video)
        var paths = StandaloneFileBrowser.OpenFilePanel("Select Video", folderPath, "mp4", false);

        if (paths.Length > 0 && !string.IsNullOrEmpty(paths[0]))
        {
            string videoPath = paths[0];
            statusText.text = "Processing: " + Path.GetFileName(videoPath);
            UnityEngine.Debug.Log("Processing .mp4 video: " + Path.GetFileName(videoPath));
            UnityEngine.Debug.Log("Application.dataPath (game path) is detected as: " + Application.dataPath);

            RunPythonProcessVideo(videoPath);
        }
    }

    // RunPythonProcessVideo not being used right now -- NOW NEED TO USE VIDEO PATH, and have it executed through the python script
    // need to modify python script so that if ran with video path as argument, then it does .mp4 analysis
    // else then just do CV for user live input
    void RunPythonProcessVideo(string videoPath)
    {
        string pythonPath = "python"; // Ensure Python is installed on the device first!
        string scriptPath = Application.dataPath + "/pose_sender.py"; // pose_sender.py script in game folder

        // setup the python execution "Process"
        ProcessStartInfo processInfo = new ProcessStartInfo
        {
            FileName = pythonPath,
            Arguments = $"\"{scriptPath}\" \"{videoPath}\"",
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true
        };

        Process process = new Process { StartInfo = processInfo };
        process.Start();
        process.WaitForExit();

        UnityEngine.Debug.Log("Python process exited! Should have sent coords");

        // string jsonPath = videoPath.Replace(".mp4", "_pose.json");
        // StartCoroutine(ReadJsonAfterProcessing(jsonPath));
    }

    IEnumerator ReadJsonAfterProcessing(string jsonPath)
    {
        while (!File.Exists(jsonPath))  // Wait for Python to generate the file
        {
            yield return new WaitForSeconds(1);
        }

        string jsonContent = File.ReadAllText(jsonPath);
        statusText.text = "Analysis complete! reference .mp4 dance JSON received.";
        UnityEngine.Debug.Log("Pose Data: " + jsonContent);
    }
}
