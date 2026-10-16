#!/usr/bin/env python3
"""
Swiftgram / Telegram-iOS Mod Patcher
Automatically injects:
1. Secret 5-second long press on 'Chats' tab -> Mod Menu (UIAlertController)
2. Ghost Mode:
   - 2.1 Hide Online Status
   - 2.2 Mark Messages as Read locally without sending receipts to server
   - 2.3 Hide Typing & Media Recording Status
   - 2.4 Delayed message sending with customizable timer (seconds)
3. Anti-Delete (retains deleted messages with '[Удалено]' tag)
4. Local Telegram Premium
5. Local NFT Star Gifts (StarGift.Unique) builder & profile injection
"""

import os
import sys
import shutil
import argparse

def log(msg, status="INFO"):
    colors = {
        "INFO": "\033[94m[*]\033[0m",
        "SUCCESS": "\033[92m[+]\033[0m",
        "WARN": "\033[93m[!]\033[0m",
        "ERROR": "\033[91m[-]\033[0m",
    }
    prefix = colors.get(status, "[*]")
    print(f"{prefix} {msg}")

def patch_file(file_path, search_pattern, replacement, description):
    if not os.path.exists(file_path):
        log(f"File not found: {file_path}", "ERROR")
        return False
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    if replacement.strip() in content:
        log(f"Already patched: {description} ({os.path.basename(file_path)})", "WARN")
        return True
        
    if search_pattern not in content:
        log(f"Target pattern not found in {file_path} for: {description}", "ERROR")
        return False
        
    new_content = content.replace(search_pattern, replacement, 1)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    log(f"Successfully patched: {description} in {os.path.basename(file_path)}", "SUCCESS")
    return True

def apply_all_patches(repo_path):
    log(f"Starting patching in repository: {repo_path}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Copy ModMenu.swift into TelegramUI
    tg_ui_sources = os.path.join(repo_path, "submodules", "TelegramUI", "Sources")
    mod_menu_src = os.path.join(base_dir, "ModMenu.swift")
    if os.path.exists(tg_ui_sources) and os.path.exists(mod_menu_src):
        dst = os.path.join(tg_ui_sources, "ModMenu.swift")
        shutil.copyfile(mod_menu_src, dst)
        log(f"Copied ModMenu.swift to {dst}", "SUCCESS")
    else:
        log("Cannot copy ModMenu.swift (directory or file missing)", "ERROR")
        return False

    # 2. Copy ModNFTGiftsManager.swift into TelegramCore
    tg_core_sources = os.path.join(repo_path, "submodules", "TelegramCore", "Sources")
    mod_nft_src = os.path.join(base_dir, "ModNFTGiftsManager.swift")
    if os.path.exists(tg_core_sources) and os.path.exists(mod_nft_src):
        dst = os.path.join(tg_core_sources, "ModNFTGiftsManager.swift")
        shutil.copyfile(mod_nft_src, dst)
        log(f"Copied ModNFTGiftsManager.swift to {dst}", "SUCCESS")
    else:
        log("Cannot copy ModNFTGiftsManager.swift (directory or file missing)", "ERROR")
        return False

    # 3. Patch Feature 1: TabBar 5.0s Long Press gesture in TelegramRootController.swift
    root_ctrl = os.path.join(tg_ui_sources, "TelegramRootController.swift")
    p1_search = """        self.rootTabController = tabBarController
        self.pushViewController(tabBarController, animated: false)
    }"""
    p1_replace = """        self.rootTabController = tabBarController
        self.pushViewController(tabBarController, animated: false)
        
        setupModMenu(rootController: self, tabBarController: tabBarController, chatListController: chatListController)
    }"""
    patch_file(root_ctrl, p1_search, p1_replace, "Feature 1: 5s Long-Press on Chats Tab -> Secret Mod Menu")

    # 4. Patch Feature 2.1: Hide Online Status in ManagedAccountPresence.swift
    presence_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "State", "ManagedAccountPresence.swift")
    p2_1_search = """    private func updatePresence(_ isOnline: Bool) {
        let request: Signal<Api.Bool, MTRpcError>
        if isOnline {"""
    p2_1_replace = """    private func updatePresence(_ isOnline: Bool) {
        var effectiveIsOnline = isOnline
        if UserDefaults.standard.bool(forKey: "mod_ghost_hide_online") {
            effectiveIsOnline = false
        }
        let request: Signal<Api.Bool, MTRpcError>
        if effectiveIsOnline {"""
    patch_file(presence_file, p2_1_search, p2_1_replace, "Feature 2.1: Ghost Mode (Hide Online Status)")

    # 5. Patch Feature 2.2 (Part 1): Read Messages without checkmarks in SynchronizePeerReadState.swift
    read_state_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "State", "SynchronizePeerReadState.swift")
    p2_2_1_search = """private func pushPeerReadState(network: Network, postbox: Postbox, stateManager: AccountStateManager, peerId: PeerId, readState: PeerReadState) -> Signal<PeerReadState, PeerReadStateValidationError> {
    if peerId.namespace == Namespaces.Peer.SecretChat {"""
    p2_2_1_replace = """private func pushPeerReadState(network: Network, postbox: Postbox, stateManager: AccountStateManager, peerId: PeerId, readState: PeerReadState) -> Signal<PeerReadState, PeerReadStateValidationError> {
    if UserDefaults.standard.bool(forKey: "mod_ghost_read_messages") {
        return .single(readState)
    }
    if peerId.namespace == Namespaces.Peer.SecretChat {"""
    patch_file(read_state_file, p2_2_1_search, p2_2_1_replace, "Feature 2.2: Ghost Mode (Block pushPeerReadState receipts)")

    # 6. Patch Feature 2.2 (Part 2): Consume Message Contents in ManagedSynchronizeConsumeMessageContentsOperations.swift
    consume_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "State", "ManagedSynchronizeConsumeMessageContentsOperations.swift")
    p2_2_2_search = """private func synchronizeConsumeMessageContents(transaction: Transaction, network: Network, stateManager: AccountStateManager, peerId: PeerId, operation: SynchronizeConsumeMessageContentsOperation) -> Signal<Void, NoError> {
    if peerId.namespace == Namespaces.Peer.CloudUser"""
    p2_2_2_replace = """private func synchronizeConsumeMessageContents(transaction: Transaction, network: Network, stateManager: AccountStateManager, peerId: PeerId, operation: SynchronizeConsumeMessageContentsOperation) -> Signal<Void, NoError> {
    if UserDefaults.standard.bool(forKey: "mod_ghost_read_messages") {
        return .complete()
    }
    if peerId.namespace == Namespaces.Peer.CloudUser"""
    patch_file(consume_file, p2_2_2_search, p2_2_2_replace, "Feature 2.2: Ghost Mode (Block synchronizeConsumeMessageContents)")

    # 7. Patch Feature 2.3: Hide Typing in ManagedLocalInputActivities.swift
    typing_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "State", "ManagedLocalInputActivities.swift")
    p2_3_search = """private func requestActivity(postbox: Postbox, network: Network, accountPeerId: PeerId, peerId: PeerId, threadId: Int64?, activity: PeerInputActivity?) -> Signal<Void, NoError> {
    return postbox.transaction { transaction -> Signal<Void, NoError> in"""
    p2_3_replace = """private func requestActivity(postbox: Postbox, network: Network, accountPeerId: PeerId, peerId: PeerId, threadId: Int64?, activity: PeerInputActivity?) -> Signal<Void, NoError> {
    if UserDefaults.standard.bool(forKey: "mod_ghost_hide_typing") {
        return .complete()
    }
    return postbox.transaction { transaction -> Signal<Void, NoError> in"""
    patch_file(typing_file, p2_3_search, p2_3_replace, "Feature 2.3: Ghost Mode (Hide Typing Status)")

    # 8. Patch Feature 2.4: Delayed Message Sending in EnqueueMessage.swift
    enqueue_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "PendingMessages", "EnqueueMessage.swift")
    p2_4_search = """public func enqueueMessages(account: Account, peerId: PeerId, messages: [EnqueueMessage]) -> Signal<[MessageId?], NoError> {"""
    p2_4_replace = """public func enqueueMessages(account: Account, peerId: PeerId, messages: [EnqueueMessage]) -> Signal<[MessageId?], NoError> {
    let delaySeconds = UserDefaults.standard.integer(forKey: "mod_delay_send_seconds")
    if delaySeconds > 0 {
        return Signal<[MessageId?], NoError>.single([])
        |> delay(Double(delaySeconds), queue: Queue.mainQueue())
        |> mapToSignal { _ -> Signal<[MessageId?], NoError> in
            return _internal_enqueueMessagesDirect(account: account, peerId: peerId, messages: messages)
        }
    }
    return _internal_enqueueMessagesDirect(account: account, peerId: peerId, messages: messages)
}

private func _internal_enqueueMessagesDirect(account: Account, peerId: PeerId, messages: [EnqueueMessage]) -> Signal<[MessageId?], NoError> {"""
    patch_file(enqueue_file, p2_4_search, p2_4_replace, "Feature 2.4: Delay Sending Timer (Configurable seconds)")

    # 9. Patch Feature 3: Anti-Delete in AccountStateManagementUtils.swift
    mgmt_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "State", "AccountStateManagementUtils.swift")
    p3_search = """            case let .DeleteMessagesWithGlobalIds(ids):
                var resourceIds: [MediaResourceId] = []
                transaction.deleteMessagesWithGlobalIds(ids, forEachMedia: { media in
                    addMessageMediaResourceIdsToRemove(media: media, resourceIds: &resourceIds)
                })
                if !resourceIds.isEmpty {
                    let _ = mediaBox.removeCachedResources(Array(Set(resourceIds)), force: true).start()
                }
                deletedMessageIds.append(contentsOf: ids.map { .global($0) })
            case let .DeleteMessages(ids):
                _internal_deleteMessages(transaction: transaction, mediaBox: mediaBox, ids: ids, manualAddMessageThreadStatsDifference: { id, add, remove in
                    addMessageThreadStatsDifference(threadKey: id, remove: remove, addedMessagePeer: nil, addedMessageId: nil, isOutgoing: false)
                })
                deletedMessageIds.append(contentsOf: ids.map { .messageId($0) })"""
    
    p3_replace = """            case let .DeleteMessagesWithGlobalIds(ids):
                if !UserDefaults.standard.bool(forKey: "mod_anti_delete") {
                    var resourceIds: [MediaResourceId] = []
                    transaction.deleteMessagesWithGlobalIds(ids, forEachMedia: { media in
                        addMessageMediaResourceIdsToRemove(media: media, resourceIds: &resourceIds)
                    })
                    if !resourceIds.isEmpty {
                        let _ = mediaBox.removeCachedResources(Array(Set(resourceIds)), force: true).start()
                    }
                    deletedMessageIds.append(contentsOf: ids.map { .global($0) })
                }
            case let .DeleteMessages(ids):
                if UserDefaults.standard.bool(forKey: "mod_anti_delete") {
                    for id in ids {
                        if let message = transaction.getMessage(id), !message.text.hasPrefix("[Удалено]") {
                            let updatedText = "[Удалено] " + (message.text.isEmpty ? "(медиа)" : message.text)
                            let _ = transaction.updateMessage(id, update: { currentMessage in
                                var storeForwardInfo: StoreMessageForwardInfo?
                                if let forwardInfo = currentMessage.forwardInfo {
                                    storeForwardInfo = StoreMessageForwardInfo(authorId: forwardInfo.author?.id, sourceId: forwardInfo.source?.id, sourceMessageId: forwardInfo.sourceMessageId, date: forwardInfo.date, authorSignature: forwardInfo.authorSignature, psaType: forwardInfo.psaType, flags: forwardInfo.flags)
                                }
                                return .update(StoreMessage(id: currentMessage.id, customStableId: nil, globallyUniqueId: currentMessage.globallyUniqueId, groupingKey: currentMessage.groupingKey, threadId: currentMessage.threadId, timestamp: currentMessage.timestamp, flags: currentMessage.flags, tags: currentMessage.tags, globalTags: currentMessage.globalTags, localTags: currentMessage.localTags, forwardInfo: storeForwardInfo, authorId: currentMessage.author?.id, text: updatedText, attributes: currentMessage.attributes, media: currentMessage.media))
                            })
                        }
                    }
                } else {
                    _internal_deleteMessages(transaction: transaction, mediaBox: mediaBox, ids: ids, manualAddMessageThreadStatsDifference: { id, add, remove in
                        addMessageThreadStatsDifference(threadKey: id, remove: remove, addedMessagePeer: nil, addedMessageId: nil, isOutgoing: false)
                    })
                    deletedMessageIds.append(contentsOf: ids.map { .messageId($0) })
                }"""
    patch_file(mgmt_file, p3_search, p3_replace, "Feature 3: Anti-Delete messages in Postbox transaction")

    # 10. Patch Feature 4 (Part 1): Local Premium in PeerUtils.swift
    peer_utils_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "Utils", "PeerUtils.swift")
    p4_1_search = """    var isPremium: Bool {
        switch self {
        case let user as TelegramUser:"""
    p4_1_replace = """    var isPremium: Bool {
        if UserDefaults.standard.bool(forKey: "mod_local_premium") {
            return true
        }
        switch self {
        case let user as TelegramUser:"""
    patch_file(peer_utils_file, p4_1_search, p4_1_replace, "Feature 4: Local Telegram Premium in PeerUtils.swift")

    # 11. Patch Feature 4 (Part 2): Local Premium in Peer.swift
    peer_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "TelegramEngine", "Peers", "Peer.swift")
    p4_2_search = """    var isPremium: Bool {
        return self._asPeer().isPremium
    }"""
    p4_2_replace = """    var isPremium: Bool {
        if UserDefaults.standard.bool(forKey: "mod_local_premium") {
            return true
        }
        return self._asPeer().isPremium
    }"""
    patch_file(peer_file, p4_2_search, p4_2_replace, "Feature 4: Local Telegram Premium in Peer.swift")

    # 12. Patch Feature 5: NFT Gifts Injection in StarGifts.swift
    gifts_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "TelegramEngine", "Payments", "StarGifts.swift")
    p5_search = """        let useMainData = (self.filter == .All && self.sorting == .date) || self.filteredCount == nil
        
        let effectiveGifts = useMainData ? self.gifts : self.filteredGifts
        let effectiveCount = useMainData ? self.count : self.filteredCount"""
    p5_replace = """        let useMainData = (self.filter == .All && self.sorting == .date) || self.filteredCount == nil
        
        var customInjectedGifts = useMainData ? self.gifts : self.filteredGifts
        if self.peerId == self.account.peerId {
            customInjectedGifts = ModNFTGiftsManager.shared.injectCustomGifts(into: customInjectedGifts, accountPeerId: self.account.peerId)
        }
        let effectiveGifts = customInjectedGifts
        let effectiveCount = (useMainData ? self.count : self.filteredCount).flatMap { $0 + Int32(ModNFTGiftsManager.shared.customGiftsCount) } ?? Int32(ModNFTGiftsManager.shared.customGiftsCount)"""
    patch_file(gifts_file, p5_search, p5_replace, "Feature 5: Local NFT Star Gifts Injection in StarGifts.swift")

    log("All patches have been successfully processed!", "SUCCESS")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Swiftgram / Telegram-iOS Mod Patcher")
    parser.add_argument("--repo-path", default=".", help="Path to cloned Telegram-iOS repository")
    args = parser.parse_args()
    
    success = apply_all_patches(os.path.abspath(args.repo_path))
    if not success:
        sys.exit(1)
