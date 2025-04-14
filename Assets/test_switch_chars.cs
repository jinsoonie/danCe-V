using UnityEngine;

public class TestCharacterSwitcher : MonoBehaviour
{
    public CharacterSkinManager skinManager;

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Alpha1)) skinManager.SetCharacter(0); // Alex
        if (Input.GetKeyDown(KeyCode.Alpha2)) skinManager.SetCharacter(1); // Ninja
        // if (Input.GetKeyDown(KeyCode.Alpha3)) skinManager.SetCharacter(2); // Kachujin
    }
}
