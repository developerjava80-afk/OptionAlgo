package com.optionalgo;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class MySQLConnector {
    private static final String URL = "jdbc:mysql://localhost:3306/kite_connect";
    private static final String USER = "root";
    private static final String PASSWORD = "hindus";

    public static Connection getConnection() throws SQLException {
        return DriverManager.getConnection(URL, USER, PASSWORD);
    }

    public static void main(String[] args) {
        try (Connection conn = getConnection()) {
            if (conn != null && !conn.isClosed()) {
                System.out.println("Connected to MySQL database successfully.");
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
}
