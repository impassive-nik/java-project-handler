package com.example;

import java.util.Scanner;

/**
 * Sample underlying java project
 *
 */
public class App 
{
    public static void main( String[] args )
    {
        Scanner sc = new Scanner(System.in);
        System.out.println("start");

        while (sc.hasNext()) {
            String cmd = sc.nextLine();
            try {
                switch (cmd) {
                case "ping":
                    System.out.println("pong");
                    break;
                case "message":
                    String author = sc.nextLine();
                    String message = sc.nextLine();
                    System.out.println(String.format("user '%s' said: %s", author, message));
                    break;
                case "quit":
                    System.out.println("quitting");
                    sc.close();
                    return;
                default:
                    System.out.println(String.format("unexpected command: %s", cmd));
                    break;
                }
            } catch (Exception e) {
                System.err.print("unexpected error");
                break;
            }
        }

        sc.close();
        System.out.println("end");
    }
}
