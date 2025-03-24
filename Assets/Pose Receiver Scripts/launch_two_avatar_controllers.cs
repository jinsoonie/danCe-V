using UnityEngine;
using System.Diagnostics;
using System.IO;
using System.Collections;

public class DanceAvatarController : MonoBehaviour
{
    void Start()
    {
        UnityEngine.Debug.Log("Unity called Python with Type 1 (Live Cam Feed).");
        // Start the live webcam feed process (Type 1)
        StartCoroutine(RunPythonProcess(true, "", false));

        // Start the reference JSON process (Type 3)
        // Update the path if your JSON file is stored elsewhere.
        string referenceJsonPath = Application.dataPath + "/Pose Receiver Scripts/reference_output.json";
        UnityEngine.Debug.Log("Unity called Python with Type 3 (Ref json sent).");
        StartCoroutine(RunPythonProcess(false, referenceJsonPath, true));
    }

    IEnumerator RunPythonProcess(bool useLiveCamera, string filePath, bool sendPreformedJson)
    {
        string pythonPath = "python"; // Make sure python is installed and in your PATH
        string scriptPath = Application.dataPath + "/Pose Receiver Scripts/pose_sender.py";
        string arguments = "";

        // Configure the arguments based on the process type.
        if (useLiveCamera)
        {
            // Type 1: live webcam feed (useLiveCamera = true, no file path, sendPreformedJson = false)
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
}
