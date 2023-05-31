using System.Text.Json;
using System.Text.Json.Serialization;
using testASPCoreMVC_2.Models;

namespace testASPCoreMVC_2.Utils
{
    public class TestJsonConverter : JsonConverter<Test>
    {
        public override Test? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            var test = new Test();
            var startDepth = reader.CurrentDepth;
            while (reader.Read())
            {
                if (reader.TokenType == JsonTokenType.EndObject && reader.CurrentDepth == startDepth)
                    return test;
                var key = "";
                if (reader.TokenType == JsonTokenType.PropertyName)
                {
                    key = reader.GetString();
                    reader.Read();
                    if (key == "rating")
                        test.Rating = reader.GetInt32();
                    if (key == "task")
                        test.Task = reader.GetString();
                    if (key == "last_result")
                        test.LastResult = reader.GetString();
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
                    test.Variants[key] = list;
                }
            }
            return test;
        }

        public override void Write(Utf8JsonWriter writer, Test value, JsonSerializerOptions options)
        {
            throw new NotImplementedException();
        }
    }
}
