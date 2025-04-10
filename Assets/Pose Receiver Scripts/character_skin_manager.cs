using UnityEngine;

public class CharacterSkinManager : MonoBehaviour
{
    public GameObject[] characterMeshes; // One GameObject per character (can contain 1 or more SkinnedMeshRenderers)
    public Avatar[] avatars;             // One Avatar per character
    public Animator animator;            // Animator on Guy_Humanoid_Ref
    public Transform sharedRootBone;     // mixamorig:Hips from the rig in Guy_Humanoid_Ref

    private int currentIndex = 0;

    public void SetCharacter(int index)
    {
        // Enable only the selected character mesh
        for (int i = 0; i < characterMeshes.Length; i++)
            characterMeshes[i].SetActive(i == index);

        // Update animator avatar
        animator.avatar = avatars[index];

        // Rebind all SkinnedMeshRenderers on the selected mesh group
        SkinnedMeshRenderer[] renderers = characterMeshes[index].GetComponentsInChildren<SkinnedMeshRenderer>();
        foreach (var smr in renderers)
        {
            RebindBones(smr, sharedRootBone);
        }

        currentIndex = index;
    }

    private void RebindBones(SkinnedMeshRenderer smr, Transform root)
    {
        // Defensive check: make sure the mesh has bones
        if (smr.bones == null || smr.bones.Length == 0)
        {
            Debug.LogWarning($"SkinnedMeshRenderer '{smr.name}' has no bones assigned. Skipping rebind.");
            return;
        }

        // Get bones from shared rig
        Transform[] rigBones = root.GetComponentsInChildren<Transform>();
        Transform[] newBones = new Transform[smr.bones.Length];

        for (int i = 0; i < newBones.Length; i++)
        {
            Transform oldBone = smr.bones[i];

            if (oldBone == null)
            {
                Debug.LogWarning($"Original bone at index {i} in mesh '{smr.name}' is null.");
                continue;
            }

            string boneName = oldBone.name;

            // Try to find that bone by name in the shared rig
            newBones[i] = System.Array.Find(rigBones, t => t.name == boneName);

            if (newBones[i] == null)
            {
                Debug.LogWarning($"Bone '{boneName}' not found in shared rig for mesh '{smr.name}'.");
            }
        }

        smr.rootBone = root;
        smr.bones = newBones;
    }

}
