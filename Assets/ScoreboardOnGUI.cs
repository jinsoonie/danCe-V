using UnityEngine;
using TMPro;

public class ScoreboardOnGUI : MonoBehaviour
{
    public PoseReceiverRightLive poseReceiver;
    public PoseSimilarityEvaluator poseSimilarity;

    public TMP_Text overallSimilarityText;
    public TMP_Text leftArmText;
    public TMP_Text rightArmText;
    public TMP_Text leftLegText;
    public TMP_Text rightLegText;
    public TMP_Text torsoText;
    public TMP_Text headText;

    void Update()
    {
        // if (poseReceiver != null)
        // {
        //     overallSimilarityText.text = $"Overall Similarity: {poseReceiver.overallSimilarity:F2}";
        //     leftArmText.text = $"Left Arm: {poseReceiver.leftArm:F2}";
        //     rightArmText.text = $"Right Arm: {poseReceiver.rightArm:F2}";
        //     leftLegText.text = $"Left Leg: {poseReceiver.leftLeg:F2}";
        //     rightLegText.text = $"Right Leg: {poseReceiver.rightLeg:F2}";
        //     torsoText.text = $"Torso: {poseReceiver.torso:F2}";
        //     headText.text = $"Head: {poseReceiver.head:F2}";
        // }
        if (poseSimilarity != null)
        {
            overallSimilarityText.text = $"Overall Similarity: {poseSimilarity.overallSimilarity:F2}";
            leftArmText.text = $"Left Arm: {poseSimilarity.leftArm:F2}";
            rightArmText.text = $"Right Arm: {poseSimilarity.rightArm:F2}";
            leftLegText.text = $"Left Leg: {poseSimilarity.leftLeg:F2}";
            rightLegText.text = $"Right Leg: {poseSimilarity.rightLeg:F2}";
            torsoText.text = $"Torso: {poseSimilarity.torso:F2}";
            headText.text = $"Head: {poseSimilarity.head:F2}";
        }
    }
}
