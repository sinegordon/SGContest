using System.Text;
using System.Text.Json.Serialization;
using testASPCoreMVC_2.Utils;

namespace testASPCoreMVC_2.Models
{
    public class UserJson
    {
        public string getUserName() { return root.UserName; }
        public UserModel getUser() { return root; }
        [JsonPropertyName("data")]
        public UserModel root { get; set; }
    }

    public class UserModel
    {
        [JsonPropertyName("user_name")]
        public string UserName { get; set; }

        [JsonPropertyName("data")]
        public Data Data { get; set; }
    }
    public class Data
    {
        [JsonPropertyName("test")]
        public IEnumerable<Test> Tests { get; set; }
    }

    [JsonConverter(typeof(TestJsonConverter))]
    public class Test
    {
        public Dictionary<string, IEnumerable<string>> Variants { get; set; }
        public int Rating { get; set; }
        public string Task { get; set; }
        public string LastResult { get; set; }
        public string getVariants()
        {
            var sb = new StringBuilder();
            foreach (var pair in Variants)
            {
                var listVariants = pair.Value.ToList();
                foreach (var variant in listVariants)
                {
                    sb.Append(variant + "\n");
                }
            }
            return sb.ToString();
        }

        public Test()
        {
            Variants = new Dictionary<string, IEnumerable<string>>();
        }

    }
}
