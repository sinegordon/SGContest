using System.Text.Json;
using System.Text.Json.Serialization;
using testASPCoreMVC_2.Areas.Admin.Models;

namespace testASPCoreMVC_2.Areas.Admin.Utils
{
    public class ProblemJsonConverter : JsonConverter<Problem>
    {
        public override Problem? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            var problem = new Problem();
            var startDepth = reader.CurrentDepth;
            while (reader.Read())
            {
                if (reader.TokenType == JsonTokenType.EndObject && reader.CurrentDepth == startDepth)
                    return problem;
                var key = "";
                if (reader.TokenType == JsonTokenType.PropertyName)
                {
                    key = reader.GetString();
                    reader.Read();
                    if (key == "rating")
                        problem.Rating = reader.GetInt32();
                    if (key == "task")
                        problem.Task = reader.GetString();
                }
                if (reader.TokenType == JsonTokenType.StartArray)
                {
                    var list = new List<string>();
                    while (reader.TokenType != JsonTokenType.EndArray)
                    {
                        reader.Read();
                        if (reader.TokenType == JsonTokenType.String)
                        {
                            list.Add(reader.GetString());
                        }
                    }
                    problem.Variants[key] = list;
                }
            }
            return problem;
        }

        public override void Write(Utf8JsonWriter writer, Problem value, JsonSerializerOptions options)
        {
            throw new NotImplementedException();
        }
    }
}
