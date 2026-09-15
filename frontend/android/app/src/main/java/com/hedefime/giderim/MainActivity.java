package com.hedefime.giderim;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(android.os.Bundle savedInstanceState) {
        registerPlugin(EncryptedStoragePlugin.class);
        super.onCreate(savedInstanceState);
    }
}
