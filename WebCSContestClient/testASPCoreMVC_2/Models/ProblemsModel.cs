using System.Text;
using System.Text.Json.Serialization;
using testASPCoreMVC_2.Areas.Admin.Utils;

namespace testASPCoreMVC_2.Areas.Admin.Models
{
    public class ProblemsModel
    {
        [JsonPropertyName("data")]
        public Data data { get; set; }

        public List<Problem> getListProblems() { 
            List<Problem> problems = new List<Problem>();
            foreach (var user in data.problems)
            {
                problems.Add(user);
            }
            return problems;
        }

        public class Data
        {
            [JsonPropertyName("problems")]
            public IEnumerable<Problem> problems { get; set; }
            //public List<dynamic> problems { get; set; }
        }
        public override string ToString()
        {
            return $"{data.problems}";
        }
    }
    [JsonConverter(typeof(ProblemJsonConverter))]
    public class Problem
    {
        public Dictionary<string, IEnumerable<string>> Variants { get; set; }
        public int Rating { get; set; }
        public string Task { get; set; }
        public string getVariants()
        {
            var sb = new StringBuilder();
            foreach (var pair in Variants)
            {
                var listVariants = pair.Value.ToList();
                foreach (var variant in listVariants)
                {
                    sb.Append(variant+"\n");
                }
            }
            return sb.ToString();
        }

        public Problem()
        {
            Variants = new Dictionary<string, IEnumerable<string>>();
        }
    }

}
