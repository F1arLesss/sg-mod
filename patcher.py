#!/usr/bin/env python3
"""
Swiftgram / Telegram-iOS Source Code Patcher for GitHub Actions & Local Builds.
Automatically applies mod features into an unmodified upstream repository:
1. Secret Mod Menu on 5.0-second long press on the "Chats" TabBar icon.
2. Ghost Mode (All toggles independently switchable):
   2.1. Hide Online status (account.updateStatus(offline: false) suppressed).
   2.2. Read messages without checkmarks (pushPeerReadState suppressed).
   2.3. Hide typing / audio recording / video recording status.
   2.4. Unseen listen for voice notes and video circles (readMessageContents suppressed).
   2.5. Configurable delayed message sending timer.
3. Anti-Delete: retain deleted messages in Postbox and mark them with [Удалено].
4. Message Edit History (Anti-Edit): retain edit history in Postbox as "Было: ... / Стало: ...".
5. Save & Forward Protected Media:
   - Bypass noforwards and isCopyProtected across all chats and channels.
   - Screen capture & recording detection bypassed (UIScreen.isCaptured suppressed).
   - View-once expiring media preserved forever with [Одноразовое / Сохранено].
   - Save to Camera Roll enabled for photos, videos, and video circles.
6. Bypass App Store Censorship & Channel Bans:
   - Filter rules and restriction overlays bypassed (channels/groups open normally).
7. Local Telegram Premium override.
8. Local NFT Star Gifts (StarGift.Unique) constructor & profile injector.
"""

import os
import sys
import shutil
import argparse


def patch_file(file_path, search_str, replace_str, description, allow_multiple=False):
    if not os.path.isfile(file_path):
        print(f"[-] Error: File not found: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if replace_str in content:
        print(f"[+] Already patched: {description}")
        return

    if search_str not in content:
        print(f"[-] Search block not found for: {description} in {file_path}")
        sys.exit(1)

    count = content.count(search_str)
    if count > 1 and not allow_multiple:
        print(f"[-] Multiple occurrences ({count}) found for: {description}")
        sys.exit(1)

    new_content = content.replace(search_str, replace_str)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[+] Successfully patched: {description} ({count} occurrence(s))")


def main():
    parser = argparse.ArgumentParser(description="Swiftgram Mod Patcher")
    parser.add_argument("--repo-path", default=".", help="Path to Telegram-iOS repository root")
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repo_path)
    workspace_root = os.path.dirname(os.path.abspath(__file__))

    print(f"[*] Starting Swiftgram Mod Patcher on {repo_path}...")

    # 1. Copy ModMenu.swift to submodules/TelegramUI/Sources/
    mod_menu_src = os.path.join(workspace_root, "ModMenu.swift")
    tg_ui_sources = os.path.join(repo_path, "submodules", "TelegramUI", "Sources")
    if os.path.isdir(tg_ui_sources):
        shutil.copy2(mod_menu_src, os.path.join(tg_ui_sources, "ModMenu.swift"))
        print(f"[+] Copied ModMenu.swift to {tg_ui_sources}")
    else:
        print(f"[-] Directory not found: {tg_ui_sources}")
        sys.exit(1)

    # 2. Copy ModNFTGiftsManager.swift to submodules/TelegramCore/Sources/
    mod_nft_src = os.path.join(workspace_root, "ModNFTGiftsManager.swift")
    tg_core_sources = os.path.join(repo_path, "submodules", "TelegramCore", "Sources")
    if os.path.isdir(tg_core_sources):
        shutil.copy2(mod_nft_src, os.path.join(tg_core_sources, "ModNFTGiftsManager.swift"))
        print(f"[+] Copied ModNFTGiftsManager.swift to {tg_core_sources}")
    else:
        print(f"[-] Directory not found: {tg_core_sources}")
        sys.exit(1)

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

    # 5. Patch Feature 2.2: Read Messages without checkmarks in SynchronizePeerReadState.swift
    read_state_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "State", "SynchronizePeerReadState.swift")
    p2_2_search = """private func pushPeerReadState(network: Network, postbox: Postbox, stateManager: AccountStateManager, peerId: PeerId, readState: PeerReadState) -> Signal<PeerReadState, PeerReadStateValidationError> {
    if peerId.namespace == Namespaces.Peer.SecretChat {"""
    p2_2_replace = """private func pushPeerReadState(network: Network, postbox: Postbox, stateManager: AccountStateManager, peerId: PeerId, readState: PeerReadState) -> Signal<PeerReadState, PeerReadStateValidationError> {
    if UserDefaults.standard.bool(forKey: "mod_ghost_read_messages") {
        return .single(readState)
    }
    if peerId.namespace == Namespaces.Peer.SecretChat {"""
    patch_file(read_state_file, p2_2_search, p2_2_replace, "Feature 2.2: Ghost Mode (Block pushPeerReadState receipts)")

    # 6. Patch Feature 2.3: Ghost Mode (Hide Typing Status) in ManagedLocalInputActivities.swift
    typing_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "State", "ManagedLocalInputActivities.swift")
    p2_3_search = """private func requestActivity(postbox: Postbox, network: Network, accountPeerId: PeerId, peerId: PeerId, threadId: Int64?, activity: PeerInputActivity?) -> Signal<Void, NoError> {
    return postbox.transaction { transaction -> Signal<Void, NoError> in"""
    p2_3_replace = """private func requestActivity(postbox: Postbox, network: Network, accountPeerId: PeerId, peerId: PeerId, threadId: Int64?, activity: PeerInputActivity?) -> Signal<Void, NoError> {
    if UserDefaults.standard.bool(forKey: "mod_ghost_hide_typing") {
        return .complete()
    }
    return postbox.transaction { transaction -> Signal<Void, NoError> in"""
    patch_file(typing_file, p2_3_search, p2_3_replace, "Feature 2.3: Ghost Mode (Hide Typing Status)")

    # 7. Patch Feature 2.4: Unseen Listen for Voice & Video Circles in ManagedSynchronizeConsumeMessageContentsOperations.swift
    consume_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "State", "ManagedSynchronizeConsumeMessageContentsOperations.swift")
    p2_4_search = """private func synchronizeConsumeMessageContents(transaction: Transaction, network: Network, stateManager: AccountStateManager, peerId: PeerId, operation: SynchronizeConsumeMessageContentsOperation) -> Signal<Void, NoError> {
    if peerId.namespace == Namespaces.Peer.CloudUser"""
    p2_4_replace = """private func synchronizeConsumeMessageContents(transaction: Transaction, network: Network, stateManager: AccountStateManager, peerId: PeerId, operation: SynchronizeConsumeMessageContentsOperation) -> Signal<Void, NoError> {
    if UserDefaults.standard.bool(forKey: "mod_ghost_read_messages") || UserDefaults.standard.bool(forKey: "mod_ghost_hide_voice_consumed") {
        return .complete()
    }
    if peerId.namespace == Namespaces.Peer.CloudUser"""
    patch_file(consume_file, p2_4_search, p2_4_replace, "Feature 2.4: Ghost Mode (Unseen listen to Voice & Circles)")

    # 8. Patch Feature 2.5: Delayed Message Sending in EnqueueMessage.swift
    enqueue_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "PendingMessages", "EnqueueMessage.swift")
    p2_5_search = """public func enqueueMessages(account: Account, peerId: PeerId, messages: [EnqueueMessage]) -> Signal<[MessageId?], NoError> {"""
    p2_5_replace = """public func enqueueMessages(account: Account, peerId: PeerId, messages: [EnqueueMessage]) -> Signal<[MessageId?], NoError> {
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
    patch_file(enqueue_file, p2_5_search, p2_5_replace, "Feature 2.5: Delay Sending Timer (Configurable seconds)")

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
                                return .update(StoreMessage(id: currentMessage.id, customStableId: nil, globallyUniqueId: currentMessage.globallyUniqueId, groupingKey: currentMessage.groupingKey, threadId: currentMessage.threadId, timestamp: currentMessage.timestamp, flags: StoreMessageFlags(currentMessage.flags), tags: currentMessage.tags, globalTags: currentMessage.globalTags, localTags: currentMessage.localTags, forwardInfo: storeForwardInfo, authorId: currentMessage.author?.id, text: updatedText, attributes: currentMessage.attributes, media: currentMessage.media))
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

    # 10. Patch Postbox Message.swift: Add withUpdatedText to StoreMessage
    postbox_msg_file = os.path.join(repo_path, "submodules", "Postbox", "Sources", "Message.swift")
    p_pb_search = """    public func withUpdatedMedia(_ media: [Media]) -> StoreMessage {
        return StoreMessage(id: self.id, customStableId: self.customStableId, globallyUniqueId: self.globallyUniqueId, groupingKey: self.groupingKey, threadId: self.threadId, timestamp: self.timestamp, flags: self.flags, tags: self.tags, globalTags: self.globalTags, localTags: self.localTags, forwardInfo: self.forwardInfo, authorId: self.authorId, text: self.text, attributes: self.attributes, media: media)
    }"""
    p_pb_replace = """    public func withUpdatedMedia(_ media: [Media]) -> StoreMessage {
        return StoreMessage(id: self.id, customStableId: self.customStableId, globallyUniqueId: self.globallyUniqueId, groupingKey: self.groupingKey, threadId: self.threadId, timestamp: self.timestamp, flags: self.flags, tags: self.tags, globalTags: self.globalTags, localTags: self.localTags, forwardInfo: self.forwardInfo, authorId: self.authorId, text: self.text, attributes: self.attributes, media: media)
    }
    
    public func withUpdatedText(_ text: String) -> StoreMessage {
        return StoreMessage(id: self.id, customStableId: self.customStableId, globallyUniqueId: self.globallyUniqueId, groupingKey: self.groupingKey, threadId: self.threadId, timestamp: self.timestamp, flags: self.flags, tags: self.tags, globalTags: self.globalTags, localTags: self.localTags, forwardInfo: self.forwardInfo, authorId: self.authorId, text: text, attributes: self.attributes, media: self.media)
    }"""
    patch_file(postbox_msg_file, p_pb_search, p_pb_replace, "Postbox: Add withUpdatedText to StoreMessage")

    # 11. Patch Feature 4: Message Edit History (Anti-Edit) in AccountStateManagementUtils.swift
    p_edit_search = """                    var updatedMedia = message.media
                    if let previousPaidContent = previousMessage.media.first(where: { $0 is TelegramMediaPaidContent }) as? TelegramMediaPaidContent, case .full = previousPaidContent.extendedMedia.first {
                        updatedMedia = previousMessage.media
                    }
                    
                    return .update(message.withUpdatedLocalTags(updatedLocalTags).withUpdatedFlags(updatedFlags).withUpdatedAttributes(updatedAttributes).withUpdatedMedia(updatedMedia))"""
    p_edit_replace = """                    var updatedMedia = message.media
                    if let previousPaidContent = previousMessage.media.first(where: { $0 is TelegramMediaPaidContent }) as? TelegramMediaPaidContent, case .full = previousPaidContent.extendedMedia.first {
                        updatedMedia = previousMessage.media
                    }
                    
                    var updatedText = message.text
                    if UserDefaults.standard.bool(forKey: "mod_anti_edit"), !previousMessage.text.isEmpty, previousMessage.text != message.text {
                        if previousMessage.text.contains("\\n---\\nСтало: ") {
                            updatedText = "\\(previousMessage.text)\\n---\\nСтало: \\(message.text)"
                        } else {
                            updatedText = "Было: \\(previousMessage.text)\\n---\\nСтало: \\(message.text)"
                        }
                    }
                    
                    return .update(message.withUpdatedLocalTags(updatedLocalTags).withUpdatedFlags(updatedFlags).withUpdatedAttributes(updatedAttributes).withUpdatedMedia(updatedMedia).withUpdatedText(updatedText))"""
    patch_file(mgmt_file, p_edit_search, p_edit_replace, "Feature 4: Message Edit History (Anti-Edit) in AccountStateManagementUtils.swift")

    # 12. Patch Feature 5 (Part 1): MessageUtils.swift (isCopyProtected & isSensitiveContent)
    msg_utils_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "Utils", "MessageUtils.swift")
    p5_1_search = """    func isCopyProtected() -> Bool {
        if self.flags.contains(.CopyProtected) {"""
    p5_1_replace = """    func isCopyProtected() -> Bool {
        if UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection") {
            return false
        }
        if self.flags.contains(.CopyProtected) {"""
    patch_file(msg_utils_file, p5_1_search, p5_1_replace, "Feature 5.1: Bypass isCopyProtected in MessageUtils.swift")

    p5_sens_search = """    func isSensitiveContent(platform: String) -> Bool {
        if let rule = self.restrictedContentAttribute?.rules.first(where: { $0.reason == "sensitive" }) {"""
    p5_sens_replace = """    func isSensitiveContent(platform: String) -> Bool {
        if UserDefaults.standard.bool(forKey: "mod_bypass_restrictions") {
            return false
        }
        if let rule = self.restrictedContentAttribute?.rules.first(where: { $0.reason == "sensitive" }) {"""
    patch_file(msg_utils_file, p5_sens_search, p5_sens_replace, "Feature 6.1: Bypass isSensitiveContent in MessageUtils.swift")

    # 13. Patch Feature 5 (Part 2): PeerUtils.swift (isCopyProtectionEnabled, restrictionText, hasSensitiveContent, isPremium)
    peer_utils_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "Utils", "PeerUtils.swift")
    p5_copy_search = """    var isCopyProtectionEnabled: Bool {
        switch self {"""
    p5_copy_replace = """    var isCopyProtectionEnabled: Bool {
        if UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection") {
            return false
        }
        switch self {"""
    patch_file(peer_utils_file, p5_copy_search, p5_copy_replace, "Feature 5.2: Bypass isCopyProtectionEnabled in PeerUtils.swift")

    p6_restr_search = """    func restrictionText(platform: String, contentSettings: ContentSettings) -> String? {
        var restrictionInfo: PeerAccessRestrictionInfo?"""
    p6_restr_replace = """    func restrictionText(platform: String, contentSettings: ContentSettings) -> String? {
        if UserDefaults.standard.bool(forKey: "mod_bypass_restrictions") {
            return nil
        }
        var restrictionInfo: PeerAccessRestrictionInfo?"""
    patch_file(peer_utils_file, p6_restr_search, p6_restr_replace, "Feature 6.2: Bypass restrictionText in PeerUtils.swift")

    p6_sens_search = """    func hasSensitiveContent(platform: String) -> Bool {
        var restrictionInfo: PeerAccessRestrictionInfo?"""
    p6_sens_replace = """    func hasSensitiveContent(platform: String) -> Bool {
        if UserDefaults.standard.bool(forKey: "mod_bypass_restrictions") {
            return false
        }
        var restrictionInfo: PeerAccessRestrictionInfo?"""
    patch_file(peer_utils_file, p6_sens_search, p6_sens_replace, "Feature 6.3: Bypass hasSensitiveContent in PeerUtils.swift")

    p4_1_search = """    var isPremium: Bool {
        switch self {
        case let user as TelegramUser:"""
    p4_1_replace = """    var isPremium: Bool {
        if UserDefaults.standard.bool(forKey: "mod_local_premium") {
            return true
        }
        switch self {
        case let user as TelegramUser:"""
    patch_file(peer_utils_file, p4_1_search, p4_1_replace, "Feature 7.1: Local Telegram Premium in PeerUtils.swift")

    # 14. Patch Feature 5 (Part 3) & Feature 6 (Part 4) & Feature 7 (Part 2): Peer.swift
    peer_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "TelegramEngine", "Peers", "Peer.swift")
    p5_peer_copy_search = """    var isCopyProtectionEnabled: Bool {
        return self._asPeer().isCopyProtectionEnabled
    }"""
    p5_peer_copy_replace = """    var isCopyProtectionEnabled: Bool {
        if UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection") {
            return false
        }
        return self._asPeer().isCopyProtectionEnabled
    }"""
    patch_file(peer_file, p5_peer_copy_search, p5_peer_copy_replace, "Feature 5.3: Bypass isCopyProtectionEnabled in Peer.swift")

    p6_peer_restr_search = """    func restrictionText(platform: String, contentSettings: ContentSettings) -> String? {
        return self._asPeer().restrictionText(platform: platform, contentSettings: contentSettings)
    }"""
    p6_peer_restr_replace = """    func restrictionText(platform: String, contentSettings: ContentSettings) -> String? {
        if UserDefaults.standard.bool(forKey: "mod_bypass_restrictions") {
            return nil
        }
        return self._asPeer().restrictionText(platform: platform, contentSettings: contentSettings)
    }"""
    patch_file(peer_file, p6_peer_restr_search, p6_peer_restr_replace, "Feature 6.4: Bypass restrictionText in Peer.swift")

    p4_2_search = """    var isPremium: Bool {
        return self._asPeer().isPremium
    }"""
    p4_2_replace = """    var isPremium: Bool {
        if UserDefaults.standard.bool(forKey: "mod_local_premium") {
            return true
        }
        return self._asPeer().isPremium
    }"""
    patch_file(peer_file, p4_2_search, p4_2_replace, "Feature 7.2: Local Telegram Premium in Peer.swift")

    # 15. Patch Feature 5 (Part 4): StoreMessage_Telegram.swift (Strip .CopyProtected on message receive)
    store_msg_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "ApiUtils", "StoreMessage_Telegram.swift")
    p5_store_search = """                if (flags & (1 << 26)) != 0 {
                    storeFlags.insert(.CopyProtected)
                }"""
    p5_store_replace = """                if (flags & (1 << 26)) != 0 && !UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection") {
                    storeFlags.insert(.CopyProtected)
                }"""
    patch_file(store_msg_file, p5_store_search, p5_store_replace, "Feature 5.4: Strip .CopyProtected flag in StoreMessage_Telegram.swift", allow_multiple=True)

    # 16. Patch Feature 5 (Part 5): ScreenCaptureDetection.swift (Disable screenshot / screen recording alerts & overlays)
    screen_cap_file = os.path.join(repo_path, "submodules", "ScreenCaptureDetection", "Sources", "ScreenCaptureDetection.swift")
    p5_sc_search1 = """public func screenCaptureEvents() -> Signal<ScreenCaptureEvent, NoError> {
    return Signal { subscriber in"""
    p5_sc_replace1 = """public func screenCaptureEvents() -> Signal<ScreenCaptureEvent, NoError> {
    if UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection") {
        return .never()
    }
    return Signal { subscriber in"""
    patch_file(screen_cap_file, p5_sc_search1, p5_sc_replace1, "Feature 5.5: Disable screenCaptureEvents in ScreenCaptureDetection.swift")

    p5_sc_search2 = """private func screenRecordingActive() -> Signal<Bool, NoError> {
    return Signal { subscriber in
        if #available(iOSApplicationExtension 11.0, iOS 11.0, *) {
            subscriber.putNext(UIScreen.main.isCaptured)"""
    p5_sc_replace2 = """private func screenRecordingActive() -> Signal<Bool, NoError> {
    return Signal { subscriber in
        if UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection") {
            subscriber.putNext(false)
            return EmptyDisposable
        }
        if #available(iOSApplicationExtension 11.0, iOS 11.0, *) {
            subscriber.putNext(UIScreen.main.isCaptured)"""
    patch_file(screen_cap_file, p5_sc_search2, p5_sc_replace2, "Feature 5.6: Disable screenRecordingActive in ScreenCaptureDetection.swift")

    p5_sc_search3 = """    public init(check: @escaping () -> Bool) {
        self.observer = ScreenshotNotificationObserver({ [weak self] in"""
    p5_sc_replace3 = """    public init(check: @escaping () -> Bool) {
        if UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection") {
            return
        }
        self.observer = ScreenshotNotificationObserver({ [weak self] in"""
    patch_file(screen_cap_file, p5_sc_search3, p5_sc_replace3, "Feature 5.7: Disable ScreenCaptureDetectionManager.init")

    # 17. Patch Feature 5 (Part 6): ManagedAutoremoveMessageOperations.swift (Retain view-once / expiring media forever)
    autoremove_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "State", "ManagedAutoremoveMessageOperations.swift")
    p5_ar_search = """                    if let message = transaction.getMessage(entry.messageId) {
                        if message.id.peerId.namespace == Namespaces.Peer.SecretChat || isRemove {
                            _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: [entry.messageId])
                        } else {"""
    p5_ar_replace = """                    if let message = transaction.getMessage(entry.messageId) {
                        if UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection") {
                            transaction.clearTimestampBasedAttribute(id: entry.messageId, tag: tag)
                            transaction.updateMessage(message.id, update: { currentMessage in
                                var storeForwardInfo: StoreMessageForwardInfo?
                                if let forwardInfo = currentMessage.forwardInfo {
                                    storeForwardInfo = StoreMessageForwardInfo(authorId: forwardInfo.author?.id, sourceId: forwardInfo.source?.id, sourceMessageId: forwardInfo.sourceMessageId, date: forwardInfo.date, authorSignature: forwardInfo.authorSignature, psaType: forwardInfo.psaType, flags: forwardInfo.flags)
                                }
                                var updatedAttributes = currentMessage.attributes
                                updatedAttributes.removeAll(where: { $0 is AutoclearTimeoutMessageAttribute || $0 is AutoremoveTimeoutMessageAttribute })
                                var text = currentMessage.text
                                if !text.contains("[Одноразовое / Сохранено]") {
                                    text = text.isEmpty ? "[Одноразовое / Сохранено]" : "[Одноразовое / Сохранено] " + text
                                }
                                return .update(StoreMessage(id: currentMessage.id, customStableId: nil, globallyUniqueId: currentMessage.globallyUniqueId, groupingKey: currentMessage.groupingKey, threadId: currentMessage.threadId, timestamp: currentMessage.timestamp, flags: StoreMessageFlags(currentMessage.flags), tags: currentMessage.tags, globalTags: currentMessage.globalTags, localTags: currentMessage.localTags, forwardInfo: storeForwardInfo, authorId: currentMessage.author?.id, text: text, attributes: updatedAttributes, media: currentMessage.media))
                            })
                        } else if message.id.peerId.namespace == Namespaces.Peer.SecretChat || isRemove {
                            _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: [entry.messageId])
                        } else {"""
    patch_file(autoremove_file, p5_ar_search, p5_ar_replace, "Feature 5.8: Retain view-once media in ManagedAutoremoveMessageOperations.swift")

    # 18. Patch Feature 5 (Part 7): ChatInterfaceStateContextMenus.swift (Save to gallery, forward, copy)
    context_menu_file = os.path.join(repo_path, "submodules", "TelegramUI", "Sources", "ChatInterfaceStateContextMenus.swift")
    p5_cm_save_search = """        if resourceAvailable, !message.containsSecretMedia && !isCopyProtected {
            var mediaReference: AnyMediaReference?
            var isVideo = false
            for media in message.effectiveMedia {
                if let image = media as? TelegramMediaImage, let _ = largestImageRepresentation(image.representations) {
                    mediaReference = ImageMediaReference.standalone(media: image).abstract
                    break
                } else if let file = media as? TelegramMediaFile, file.isVideo {
                    mediaReference = FileMediaReference.standalone(media: file).abstract
                    isVideo = true
                    break
                }
            }"""
    p5_cm_save_replace = """        let allowMediaSaving = (!message.containsSecretMedia && !isCopyProtected) || UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection")
        if resourceAvailable, allowMediaSaving {
            var mediaReference: AnyMediaReference?
            var isVideo = false
            for media in message.effectiveMedia {
                if let image = media as? TelegramMediaImage, let _ = largestImageRepresentation(image.representations) {
                    mediaReference = ImageMediaReference.standalone(media: image).abstract
                    break
                } else if let file = media as? TelegramMediaFile, (file.isVideo || file.isInstantVideo) {
                    mediaReference = FileMediaReference.standalone(media: file).abstract
                    isVideo = true
                    break
                }
            }"""
    patch_file(context_menu_file, p5_cm_save_search, p5_cm_save_replace, "Feature 5.9: Save to Camera Roll for circles & protected media")

    p5_cm_iscopy_search1 = """    let isCopyProtected = chatPresentationInterfaceState.copyProtectionEnabled || message.isCopyProtected()
    let replacementMessage = message.activeEphemeralReplacementMessage"""
    p5_cm_iscopy_replace1 = """    let isCopyProtected = (chatPresentationInterfaceState.copyProtectionEnabled || message.isCopyProtected()) && !UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection")
    let replacementMessage = message.activeEphemeralReplacementMessage"""
    patch_file(context_menu_file, p5_cm_iscopy_search1, p5_cm_iscopy_replace1, "Feature 5.10: Bypass isCopyProtected in ephemeral context menu")

    p5_cm_iscopy_search2 = """        let isCopyProtected = chatPresentationInterfaceState.copyProtectionEnabled || message.isCopyProtected()
        if !messageText.isEmpty || richMessageMarkdown != nil || (resourceAvailable && isImage) || diceEmoji != nil {"""
    p5_cm_iscopy_replace2 = """        let isCopyProtected = (chatPresentationInterfaceState.copyProtectionEnabled || message.isCopyProtected()) && !UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection")
        if !messageText.isEmpty || richMessageMarkdown != nil || (resourceAvailable && isImage) || diceEmoji != nil {"""
    patch_file(context_menu_file, p5_cm_iscopy_search2, p5_cm_iscopy_replace2, "Feature 5.11: Enable copy text for protected messages")

    p5_cm_peercopy_search = """        func isPeerCopyProtected(_ peerId: EnginePeer.Id) -> Bool? {
            let copyProtection = copyProtectionMap[peerId]"""
    p5_cm_peercopy_replace = """        func isPeerCopyProtected(_ peerId: EnginePeer.Id) -> Bool? {
            if UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection") {
                return nil
            }
            let copyProtection = copyProtectionMap[peerId]"""
    patch_file(context_menu_file, p5_cm_peercopy_search, p5_cm_peercopy_replace, "Feature 5.12: Bypass isPeerCopyProtected helper")

    p5_cm_actions_search = """                if message.isCopyProtected() || message.containsSecretMedia {
                    isCopyProtected = true
                }
                
                if isPeerCopyProtected(message.id.peerId) == true {
                    isCopyProtected = true
                }"""
    p5_cm_actions_replace = """                if !UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection") {
                    if message.isCopyProtected() || message.containsSecretMedia {
                        isCopyProtected = true
                    }
                    
                    if isPeerCopyProtected(message.id.peerId) == true {
                        isCopyProtected = true
                    }
                }"""
    patch_file(context_menu_file, p5_cm_actions_search, p5_cm_actions_replace, "Feature 5.13: Bypass isCopyProtected in message actions")

    p5_cm_fwd_search = """                    if !isForwardingDisabled && !message.containsSecretMedia && !isAction && !isCopyProtected && !isShareProtected && !(message.flags.isSending || message.flags.contains(.Failed)) {
                        optionsMap[id]!.insert(.forward)
                    }"""
    p5_cm_fwd_replace = """                    let canForwardEphemeral = (!isForwardingDisabled && !message.containsSecretMedia && !isAction && !isCopyProtected && !isShareProtected && !(message.flags.isSending || message.flags.contains(.Failed))) || UserDefaults.standard.bool(forKey: "mod_bypass_copy_protection")
                    if canForwardEphemeral {
                        optionsMap[id]!.insert(.forward)
                    }"""
    patch_file(context_menu_file, p5_cm_fwd_search, p5_cm_fwd_replace, "Feature 5.14: Enable forward for ephemeral & protected messages")

    # 19. Patch Feature 6 (Part 5): PlatformRestrictionMatching.swift
    plat_file = os.path.join(repo_path, "submodules", "PlatformRestrictionMatching", "Sources", "PlatformRestrictionMatching.swift")
    p6_plat_search1 = """    func restrictionReason(platform: String, contentSettings: ContentSettings) -> String? {
        if let attribute = self.restrictedContentAttribute {"""
    p6_plat_replace1 = """    func restrictionReason(platform: String, contentSettings: ContentSettings) -> String? {
        if UserDefaults.standard.bool(forKey: "mod_bypass_restrictions") {
            return nil
        }
        if let attribute = self.restrictedContentAttribute {"""
    patch_file(plat_file, p6_plat_search1, p6_plat_replace1, "Feature 6.5: Bypass restrictionReason in PlatformRestrictionMatching.swift")

    p6_plat_search2 = """    func platformText(platform: String, contentSettings: ContentSettings) -> String? {
        for rule in self.rules {"""
    p6_plat_replace2 = """    func platformText(platform: String, contentSettings: ContentSettings) -> String? {
        if UserDefaults.standard.bool(forKey: "mod_bypass_restrictions") {
            return nil
        }
        for rule in self.rules {"""
    patch_file(plat_file, p6_plat_search2, p6_plat_replace2, "Feature 6.6: Bypass platformText in PlatformRestrictionMatching.swift")

    # 20. Patch Feature 6 (Part 6): ProcessedPeerRestrictionText.swift
    proc_restr_file = os.path.join(repo_path, "submodules", "TelegramUI", "Sources", "ProcessedPeerRestrictionText.swift")
    p6_proc_search = """func processedPeerRestrictionText(_ text: String) -> String {
    if let range = text.range(of: ":") {"""
    p6_proc_replace = """func processedPeerRestrictionText(_ text: String) -> String {
    if UserDefaults.standard.bool(forKey: "mod_bypass_restrictions") {
        return ""
    }
    if let range = text.range(of: ":") {"""
    patch_file(proc_restr_file, p6_proc_search, p6_proc_replace, "Feature 6.7: Bypass processedPeerRestrictionText in TelegramUI")

    # 21. Patch Feature 8: NFT Gifts Injection in StarGifts.swift
    gifts_file = os.path.join(repo_path, "submodules", "TelegramCore", "Sources", "TelegramEngine", "Payments", "StarGifts.swift")
    p8_search = """        let useMainData = (self.filter == .All && self.sorting == .date) || self.filteredCount == nil
        
        let effectiveGifts = useMainData ? self.gifts : self.filteredGifts
        let effectiveCount = useMainData ? self.count : self.filteredCount"""
    p8_replace = """        let useMainData = (self.filter == .All && self.sorting == .date) || self.filteredCount == nil
        
        var effectiveGifts = useMainData ? self.gifts : self.filteredGifts
        let effectiveCount = useMainData ? self.count : self.filteredCount
        
        let customGifts = ModNFTGiftsManager.shared.getCustomGifts()
        if !customGifts.isEmpty {
            var combined = customGifts
            combined.append(contentsOf: effectiveGifts)
            effectiveGifts = combined
        }"""
    patch_file(gifts_file, p8_search, p8_replace, "Feature 8: Local NFT Gifts injection in ProfileGiftsContext")

    # 22. Patch Telegram/BUILD: App Icons compatibility (bypass Xcode 26 Icon Composer requirement)
    tg_build_file = os.path.join(repo_path, "Telegram", "BUILD")
    if os.path.isfile(tg_build_file):
        p22_search_folders = 'composer_icon_folders = ["Telegram"]'
        p22_replace_folders = 'composer_icon_folders = []'
        patch_file(tg_build_file, p22_search_folders, p22_replace_folders, "Compatibility: Empty composer_icon_folders")

        p22_search_app_icons = """    app_icons = [ ":{}_icon".format(name) for name in composer_icon_folders ],
    alternate_icons = [
        ":{}".format(name) for name in alternate_icon_folders
    ],
    resources = [
        ":LaunchScreen",
        #":DefaultAppIcon",
    ],"""
        p22_replace_app_icons = """    alternate_icons = [
        ":{}".format(name) for name in alternate_icon_folders
    ],
    resources = [
        ":LaunchScreen",
        ":DefaultAppIcon",
    ],"""
        patch_file(tg_build_file, p22_search_app_icons, p22_replace_app_icons, "Compatibility: Restore DefaultAppIcon and bypass Xcode 26 Icon Composer requirement")

    # 23. Patch versions.json: align xcode version
    versions_file = os.path.join(repo_path, "versions.json")
    if os.path.isfile(versions_file):
        try:
            import json
            with open(versions_file, "r", encoding="utf-8") as f:
                v_data = json.load(f)
            v_data["xcode"] = "16.2"
            v_data["deploy_xcode"] = "16.2"
            with open(versions_file, "w", encoding="utf-8") as f:
                json.dump(v_data, f, indent=4)
            print("[+] Successfully updated versions.json to Xcode 16.2")
        except Exception as e:
            print(f"[!] Warning updating versions.json: {e}")

    # 24. Patch WebProxyTransport for Xcode 16 / iOS 18.2 SDK compatibility
    carrier_file = os.path.join(repo_path, "submodules", "WebProxyTransport", "Sources", "WebProxyWebViewCarrier.swift")
    if os.path.isfile(carrier_file):
        patch_file(carrier_file, "import WebKit", "@preconcurrency import WebKit", "Compatibility: @preconcurrency import WebKit in WebProxyWebViewCarrier.swift")

        p24_search_panel = """    @available(macOS 10.12, iOS 18.4, *)
    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        completionHandler(nil)
    }"""
        p24_replace_panel = """    /*
    @available(macOS 10.12, iOS 18.4, *)
    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        completionHandler(nil)
    }
    */"""
        patch_file(carrier_file, p24_search_panel, p24_replace_panel, "Compatibility: Comment out WKOpenPanelParameters for iOS SDK 18.2 compatibility")

    attachment_file = os.path.join(repo_path, "submodules", "WebProxyTransport", "Sources", "WebProxyViewAttachment.swift")
    if os.path.isfile(attachment_file):
        patch_file(attachment_file, "import WebKit", "@preconcurrency import WebKit", "Compatibility: @preconcurrency import WebKit in WebProxyViewAttachment.swift")

    hardening_file = os.path.join(repo_path, "submodules", "WebProxyTransport", "Sources", "WebProxyWebViewHardening.swift")
    if os.path.isfile(hardening_file):
        patch_file(hardening_file, "import WebKit", "@preconcurrency import WebKit", "Compatibility: @preconcurrency import WebKit in WebProxyWebViewHardening.swift")

    # 25. Patch submodules/WebProxyTransport/BUILD: remove -warnings-as-errors
    wpt_build_file = os.path.join(repo_path, "submodules", "WebProxyTransport", "BUILD")
    if os.path.isfile(wpt_build_file):
        patch_file(wpt_build_file, '"-warnings-as-errors",', '# "-warnings-as-errors",', "Compatibility: disable -warnings-as-errors in WebProxyTransport")

    # 26. Patch Make.py: disable dsyms, watchos_cpus, and Rust lto=fat to speed up build by 2-3x
    make_file = os.path.join(repo_path, "build-system", "Make", "Make.py")
    if os.path.isfile(make_file):
        patch_file(make_file, "'--@rules_rust//rust/settings:lto=fat',", "'--@rules_rust//rust/settings:lto=off',", "Optimization: disable Rust fat LTO in Make.py")

        p26_search_config = """                # Always build universal Watch binaries.
                '--watchos_cpus=arm64_32',

                # Generate DSYM files when building.
                '--apple_generate_dsym',

                # Require DSYM files as build output.
                '--output_groups=+dsyms',"""
        p26_replace_config = """                # Disabled for faster CI builds:
                # '--watchos_cpus=arm64_32',
                # '--apple_generate_dsym',
                # '--output_groups=+dsyms',"""
        patch_file(make_file, p26_search_config, p26_replace_config, "Optimization: disable watchos_cpus and dsyms in Make.py")

    print("[SUCCESS] All patch operations applied cleanly.")


if __name__ == "__main__":
    main()
