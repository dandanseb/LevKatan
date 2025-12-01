using System;
using Npgsql;

// NOTE:
// This is the tests file to connect to PostgreSQL
// Program_logic.cs contains the main API logic
// Whatever file named Program.cs is the one to run

namespace Backend
{
    public class DatabaseConnection
    {
        public static NpgsqlConnection ConnectToDb()
        {
            // --- CONFIGURATION ---
            string host = "172.29.112.1";   // Change if your DB is hosted elsewhere
            string port = "5432";           // Default PostgreSQL port
            string dbName = "LevKatan";     // Your specific database name
            string user = "dansebbah2@gmail.com";       // Default superuser
            
            // TODO: REPLACE THIS WITH YOUR REAL PGADMIN PASSWORD
            string password = "rebeccawife"; 

            string connectionString = $"Host={host};Port={port};Database={dbName};Username={user};Password={password};";

            Console.WriteLine($"Attempting to connect to: {host}:{port}/{dbName}...");

            try
            {
                var conn = new NpgsqlConnection(connectionString);
                conn.Open();
                Console.WriteLine("--------------------------------------------------");
                Console.WriteLine("✅ SUCCESS! Connected to PostgreSQL successfully!");
                Console.WriteLine("--------------------------------------------------");
                return conn;
            }
            catch (PostgresException ex)
            {
                 Console.WriteLine("❌ DATABASE ERROR: " + ex.MessageText);
                 if(ex.SqlState == "3D000") Console.WriteLine("-> Hint: The database 'LevKatan' does not exist.");
                 if(ex.SqlState == "28P01") Console.WriteLine("-> Hint: Password authentication failed.");
                 return null;
            }
            catch (NpgsqlException ex)
            {
                Console.WriteLine("❌ CONNECTION ERROR: " + ex.Message);
                Console.WriteLine("-> Hint: Is the Server running? Is the Port correct?");
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine("❌ UNEXPECTED ERROR: " + ex.Message);
                return null;
            }
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            var connection = DatabaseConnection.ConnectToDb();

            if (connection != null)
            {
                // Simple test: Get the server version
                using var cmd = new NpgsqlCommand("SELECT version();", connection);
                var version = cmd.ExecuteScalar();
                Console.WriteLine("Server Version: " + version);

                connection.Close();
                Console.WriteLine("Connection closed. You are ready to build the API.");
            }
            else 
            {
                Console.WriteLine("--------------------------------------------------");
                Console.WriteLine("⚠️  CONNECTION FAILED");
                Console.WriteLine("Please check your Password, Port, and if PostgreSQL is running.");
                Console.WriteLine("--------------------------------------------------");
            }
        }
    }
}