import Foundation
import UIKit
import TelegramCore
import Display
import TelegramPresentationData

public final class ModMenuHandler: NSObject, UIGestureRecognizerDelegate {
    public static let shared = ModMenuHandler()
    
    private weak var rootController: UIViewController?
    private weak var chatListController: UIViewController?
    
    public func attach(rootController: UIViewController, tabBarView: UIView, chatListController: UIViewController) {
        self.rootController = rootController
        self.chatListController = chatListController
        
        let longPress = UILongPressGestureRecognizer(target: self, action: #selector(self.handleLongPress(_:)))
        longPress.minimumPressDuration = 5.0
        longPress.cancelsTouchesInView = false
        longPress.delegate = self
        tabBarView.addGestureRecognizer(longPress)
    }
    
    public func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer, shouldRecognizeSimultaneouslyWith otherGestureRecognizer: UIGestureRecognizer) -> Bool {
        return true
    }
    
    @objc private func handleLongPress(_ gesture: UILongPressGestureRecognizer) {
        guard gesture.state == .began else {
            return
        }
        
        let generator = UIImpactFeedbackGenerator(style: .heavy)
        generator.prepare()
        generator.impactOccurred()
        
        if let root = self.rootController {
            self.showModMenu(from: root)
        }
    }
    
    public func showModMenu(from presenter: UIViewController) {
        let hideOnline = UserDefaults.standard.bool(forKey: "mod_ghost_hide_online")
        let readMessages = UserDefaults.standard.bool(forKey: "mod_ghost_read_messages")
        let hideTyping = UserDefaults.standard.bool(forKey: "mod_ghost_hide_typing")
        let delaySeconds = UserDefaults.standard.integer(forKey: "mod_delay_send_seconds")
        let antiDelete = UserDefaults.standard.bool(forKey: "mod_anti_delete")
        let localPremium = UserDefaults.standard.bool(forKey: "mod_local_premium")
        let giftsCount = ModNFTGiftsManager.shared.customGiftsCount
        
        let alert = UIAlertController(
            title: "⚡ Swiftgram Mod Menu",
            message: "Настройки модификаций клиента",
            preferredStyle: .actionSheet
        )
        
        // 2.1 Hide Online
        let onlineTitle = "👻 [Призрак] Скрытие онлайн: " + (hideOnline ? "🟢 ВКЛ" : "⚪ ВЫКЛ")
        alert.addAction(UIAlertAction(title: onlineTitle, style: .default, handler: { [weak self] _ in
            UserDefaults.standard.set(!hideOnline, forKey: "mod_ghost_hide_online")
            self?.feedback()
            self?.showModMenu(from: presenter)
        }))
        
        // 2.2 Read Messages without mark
        let readTitle = "👻 [Призрак] Чтение без отметки: " + (readMessages ? "🟢 ВКЛ" : "⚪ ВЫКЛ")
        alert.addAction(UIAlertAction(title: readTitle, style: .default, handler: { [weak self] _ in
            UserDefaults.standard.set(!readMessages, forKey: "mod_ghost_read_messages")
            self?.feedback()
            self?.showModMenu(from: presenter)
        }))
        
        // 2.3 Hide Typing
        let typingTitle = "👻 [Призрак] Скрытие набора текста: " + (hideTyping ? "🟢 ВКЛ" : "⚪ ВЫКЛ")
        alert.addAction(UIAlertAction(title: typingTitle, style: .default, handler: { [weak self] _ in
            UserDefaults.standard.set(!hideTyping, forKey: "mod_ghost_hide_typing")
            self?.feedback()
            self?.showModMenu(from: presenter)
        }))
        
        // 2.4 Delayed Send
        let delayTitle = "⏱️ [Призрак] Задержка отправки: " + (delaySeconds > 0 ? "\(delaySeconds) сек." : "ВЫКЛ")
        alert.addAction(UIAlertAction(title: delayTitle, style: .default, handler: { [weak self] _ in
            self?.promptDelayTimer(from: presenter)
        }))
        
        // 3. Anti-Delete
        let antiDeleteTitle = "🗑️ Анти-удаление сообщений: " + (antiDelete ? "🟢 ВКЛ" : "⚪ ВЫКЛ")
        alert.addAction(UIAlertAction(title: antiDeleteTitle, style: .default, handler: { [weak self] _ in
            UserDefaults.standard.set(!antiDelete, forKey: "mod_anti_delete")
            self?.feedback()
            self?.showModMenu(from: presenter)
        }))
        
        // 4. Local Telegram Premium
        let premiumTitle = "⭐ Локальный Telegram Premium: " + (localPremium ? "🟢 ВКЛ" : "⚪ ВЫКЛ")
        alert.addAction(UIAlertAction(title: premiumTitle, style: .default, handler: { [weak self] _ in
            UserDefaults.standard.set(!localPremium, forKey: "mod_local_premium")
            self?.feedback()
            self?.showModMenu(from: presenter)
        }))
        
        // 5. NFT Star Gifts Builder
        let giftsTitle = "🎁 Конструктор NFT-подарков (в профиле: \(giftsCount))"
        alert.addAction(UIAlertAction(title: giftsTitle, style: .default, handler: { [weak self] _ in
            self?.showNFTGiftsBuilder(from: presenter)
        }))
        
        alert.addAction(UIAlertAction(title: "Закрыть", style: .cancel, handler: nil))
        
        if let popover = alert.popoverPresentationController {
            popover.sourceView = presenter.view
            popover.sourceRect = CGRect(x: presenter.view.bounds.midX, y: presenter.view.bounds.maxY - 100, width: 0, height: 0)
        }
        
        presenter.present(alert, animated: true, completion: nil)
    }
    
    private func promptDelayTimer(from presenter: UIViewController) {
        let currentDelay = UserDefaults.standard.integer(forKey: "mod_delay_send_seconds")
        let prompt = UIAlertController(
            title: "⏱️ Отложенная отправка",
            message: "Задайте количество секунд задержки отправки сообщений (0 — отключено, либо любое число: 5, 10, 30 и т.д.):",
            preferredStyle: .alert
        )
        prompt.addTextField { textField in
            textField.keyboardType = .numberPad
            textField.placeholder = "0"
            textField.text = currentDelay > 0 ? "\(currentDelay)" : ""
        }
        prompt.addAction(UIAlertAction(title: "Сохранить", style: .default, handler: { [weak self] _ in
            let text = prompt.textFields?.first?.text ?? ""
            let seconds = Int(text) ?? 0
            UserDefaults.standard.set(max(0, seconds), forKey: "mod_delay_send_seconds")
            self?.feedback()
            self?.showModMenu(from: presenter)
        }))
        prompt.addAction(UIAlertAction(title: "Отмена", style: .cancel, handler: { [weak self] _ in
            self?.showModMenu(from: presenter)
        }))
        presenter.present(prompt, animated: true, completion: nil)
    }
    
    private func showNFTGiftsBuilder(from presenter: UIViewController) {
        let giftsCount = ModNFTGiftsManager.shared.customGiftsCount
        let alert = UIAlertController(
            title: "🎁 Конструктор NFT-подарков",
            message: "Создавайте любые уникальные подарки (StarGift.Unique) и добавляйте их в свой профиль. Сейчас в профиле: \(giftsCount) шт.",
            preferredStyle: .actionSheet
        )
        
        let presets: [(name: String, model: String, inner: Int32, outer: Int32, pattern: Int32, text: Int32)] = [
            ("🧢 Durov's Cap #777", "DurovsCap", 0x1F2A44, 0x0E1424, 0x4B96FF, 0xFFFFFF),
            ("🐸 Plush Pepe #1", "PlushPepe", 0x224227, 0x0F2113, 0x48C95F, 0xFFFFFF),
            ("💎 Diamond Ring #999", "DiamondRing", 0x1E3347, 0x0B1624, 0x64C4ED, 0xFFFFFF),
            ("🏆 Golden Trophy #100", "GoldTrophy", 0x423512, 0x241C06, 0xF2C94C, 0xFFFFFF),
            ("💀 Cyber Skull #1337", "CyberSkull", 0x36163D, 0x1A0821, 0xBB6BD9, 0xFFFFFF),
            ("👑 Imperial Crown #7", "ImperialCrown", 0x3D1B24, 0x21080F, 0xEB5757, 0xFFFFFF)
        ]
        
        for preset in presets {
            alert.addAction(UIAlertAction(title: "➕ Добавить: \(preset.name)", style: .default, handler: { [weak self] _ in
                let parts = preset.name.components(separatedBy: " #")
                let title = parts.first ?? preset.name
                let num = Int32(parts.count > 1 ? (Int(parts[1]) ?? 1) : 1)
                
                ModNFTGiftsManager.shared.addGift(
                    title: title,
                    number: num,
                    modelName: preset.model,
                    backdropId: 1,
                    innerColor: preset.inner,
                    outerColor: preset.outer,
                    patternColor: preset.pattern,
                    textColor: preset.text
                )
                self?.feedback()
                self?.showSuccessNotice(from: presenter, message: "Подарок «\(preset.name)» успешно добавлен в ваш профиль!")
            }))
        }
        
        alert.addAction(UIAlertAction(title: "🗑️ Очистить все созданные подарки", style: .destructive, handler: { [weak self] _ in
            ModNFTGiftsManager.shared.clearGifts()
            self?.feedback()
            self?.showSuccessNotice(from: presenter, message: "Все созданные подарки очищены.")
        }))
        
        alert.addAction(UIAlertAction(title: "⬅️ Назад в меню", style: .cancel, handler: { [weak self] _ in
            self?.showModMenu(from: presenter)
        }))
        
        if let popover = alert.popoverPresentationController {
            popover.sourceView = presenter.view
            popover.sourceRect = CGRect(x: presenter.view.bounds.midX, y: presenter.view.bounds.maxY - 100, width: 0, height: 0)
        }
        
        presenter.present(alert, animated: true, completion: nil)
    }
    
    private func showSuccessNotice(from presenter: UIViewController, message: String) {
        let alert = UIAlertController(title: "Готово", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default, handler: { [weak self] _ in
            self?.showModMenu(from: presenter)
        }))
        presenter.present(alert, animated: true, completion: nil)
    }
    
    private func feedback() {
        let generator = UIImpactFeedbackGenerator(style: .medium)
        generator.prepare()
        generator.impactOccurred()
    }
}

public func setupModMenu(rootController: UIViewController, tabBarController: UIViewController, chatListController: UIViewController) {
    ModMenuHandler.shared.attach(
        rootController: rootController,
        tabBarView: tabBarController.view,
        chatListController: chatListController
    )
}
