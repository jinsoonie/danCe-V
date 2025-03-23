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

            SceneManager.LoadSceneAsync("Dance Avatar Scene");

            RunPythonProcessVideo(videoPath);
        }
    }

    // RunPythonProcessVideo used for if specified videoPath .mp4 reference video
    // ensure non-blocking (unity keeps running to receive .mp4 reference video .json coords)
    void RunPythonProcessVideo(string videoPath)
    {
        string pythonPath = "python"; // Ensure Python is installed on the device first!
        string scriptPath = Application.dataPath + "/Pose Receiver Scripts/pose_sender.py"; // pose_sender.py script in game folder

        UnityEngine.Debug.Log($"Running Python Script: {scriptPath}");

        // setup the python execution "Process"
        // False for USE_LIVE_CAMERA, False for send_preformed_json (since analyzing ref .mp4 here, not sending_preformed_json)
        // CAN CHANGE FOR TESTING THE MAIN MENU SCENE, HOWEVER
        ProcessStartInfo processInfo = new ProcessStartInfo
        {
            FileName = pythonPath,
            Arguments = $"\"{scriptPath}\" False \"{videoPath}\" False",
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = false
        };

        Process process = new Process { StartInfo = processInfo };

        // Attach asynchronous event handlers
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

        process.BeginOutputReadLine(); // Asynchronously read output
        process.BeginErrorReadLine();  // Asynchronously read error
        UnityEngine.Debug.Log("Python process started asynchronously! Unity will keep running.");

        // string jsonPath = videoPath.Replace(".mp4", "_pose.json");
        // StartCoroutine(ReadJsonAfterProcessing(jsonPath));

        ////////////////// ADDDDDDDDDDDD CODE FOR OTHER PROCESSING PYTHON pose_sender.py CALLS for 2 avatars!! (2 pose_sender.py instances, 1for ref .mp4, 1 for live cap)
    }

    // IEnumerator ReadJsonAfterProcessing(string jsonPath)
    // {
    //     while (!File.Exists(jsonPath))  // Wait for Python to generate the file
    //     {
    //         yield return new WaitForSeconds(1);
    //     }

    //     string jsonContent = File.ReadAllText(jsonPath);
    //     statusText.text = "Analysis complete! reference .mp4 dance JSON received.";
    //     UnityEngine.Debug.Log("Pose Data: " + jsonContent);
    // }
}
