namespace testASPCoreMVC_2.Enums
{
    using System.ComponentModel.DataAnnotations; // для атрибута Display

    public enum Languages
    {
        [Display(Name = "python3")]
        python,
        [Display(Name = "c#")]
        cs,
        [Display(Name = "c")]
        c,
        [Display(Name = "c++")]
        cpp
    }
}
