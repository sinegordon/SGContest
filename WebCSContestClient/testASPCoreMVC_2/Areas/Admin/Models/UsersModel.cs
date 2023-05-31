using System.Text.Json.Serialization;
using testASPCoreMVC_2.Models;

namespace testASPCoreMVC_2.Areas.Admin.Models
{
    public class UsersModel
    {
        public List<string> getUserNames()
        {
            List<string> names = new List<string>();
            foreach (var user in root)
            {
                names.Add(user.UserName);
            }
            return names;
        }

        [JsonPropertyName("data")]
        public List<UserModel> root { get; set; }
    }
}
